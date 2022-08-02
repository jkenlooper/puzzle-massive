import time
import logging

import requests

from api.tools import formatPieceMovementString

logger = logging.getLogger(__name__)

# TODO: make these configurable in the site.cfg, they could also be configurable
# per puzzle.
SINGLE_STACK_THRESHOLD = 1
GROUP_STACK_THRESHOLD = 1
STACK_COST_THRESHOLD = 2
STACK_LIMIT = 4
OVERLAP_THRESHOLD = 0.5


def get_bbox_area(bbox):
    return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])


class Proximity:
    """
    Count the pieces in proximity on the piece that moved.

    Piece proximity threshold is based on count of adjacent pieces.
    """

    def __init__(
        self,
        redis_connection,
        proximity_idx,
        origin_bboxes,
        puzzle_data,
        piece_properties,
        config,
    ):
        self.config = config
        logger.setLevel(logging.DEBUG if config["DEBUG"] else logging.INFO)
        self.redis_connection = redis_connection
        self.proximity_idx = proximity_idx
        self.piece_properties = piece_properties
        self.puzzle_data = puzzle_data
        self.proximity_init_time = time.time()
        self.internal_origin_bboxes = origin_bboxes

        # Skip updating all pieces initially as it is not optimal for larger
        # puzzles.
        # self.reassess_all()

    def process(self, user, puzzle, piece, origin_x, origin_y, x, y):
        # rotate is not implemented yet; leaving origin_r as 0 for now.
        stacked_piece_ids = set()
        reset_stacked_ids = set()
        origin_r = 0
        logger.debug(
            f"proximity process {user}, {puzzle}, {piece}, {origin_x}, {origin_y}, {x}, {y}"
        )
        w = self.piece_properties[piece]["w"]
        h = self.piece_properties[piece]["h"]
        origin_piece_bbox = (
            origin_x,
            origin_y,
            origin_x + w,
            origin_y + h,
        )
        piece_bbox = (
            x,
            y,
            x + w,
            y + h,
        )
        pcfixed = set(map(int, self.redis_connection.smembers(f"pcfixed:{puzzle}")))

        piece_group = int(
            self.redis_connection.hget(f"pc:{puzzle}:{piece}", "g") or piece
        )
        pcg = set(
            map(int, self.redis_connection.smembers(f"pcg:{puzzle}:{piece_group}"))
        )
        ignore_piece_ids = pcfixed.union(pcg)

        # Reassess stacked pieces that were intersecting with the piece origin
        reset_stacked_ids.add(piece)
        self.move_piece(piece, piece_bbox)
        origin_stack_counts = self.get_stack_counts(
            origin_piece_bbox, ignore_piece_ids=pcfixed
        )
        for piece_id, stack_count in origin_stack_counts.items():
            if piece_id == piece:
                reset_stacked_ids.add(piece_id)
            elif stack_count <= SINGLE_STACK_THRESHOLD:
                reset_stacked_ids.add(piece_id)

        def reject_piece_move():
            success = False
            logger.debug(f"Exceeded stack limit; reject piece move for {piece}")
            r = requests.patch(
                "http://{HOSTPUBLISH}:{PORTPUBLISH}/internal/puzzle/{puzzle_id}/piece/{piece}/move/".format(
                    HOSTPUBLISH=self.config["HOSTPUBLISH"],
                    PORTPUBLISH=self.config["PORTPUBLISH"],
                    puzzle_id=self.puzzle_data["puzzle_id"],
                    piece=piece,
                ),
                json={
                    "x": origin_x,
                    "y": origin_y,
                    "r": origin_r,
                },
            )
            if r.status_code >= 400:
                # Could be caused by the puzzle completing after the initial
                # request.
                logger.info(
                    "Ignoring error when attempting to reject piece movement on possibly completed puzzle"
                )
            else:
                # Keep the proximity idx in sync with the rejected piece move
                self.move_piece(piece, origin_piece_bbox)
                success = True
            return success

        # Reassess stacked pieces that are now intersecting with the piece after
        # it moved.
        piece_move_rejected = False
        past_stack_cost_threshold = False
        target_stack_counts = self.get_stack_counts(
            piece_bbox, ignore_piece_ids=ignore_piece_ids
        )
        for piece_id, stack_count in target_stack_counts.items():
            if stack_count > STACK_LIMIT:
                piece_move_rejected = reject_piece_move()
                break
            if piece_id in ignore_piece_ids:
                continue
            if stack_count > SINGLE_STACK_THRESHOLD:
                stacked_piece_ids.add(piece_id)
            if stack_count > STACK_COST_THRESHOLD:
                past_stack_cost_threshold = True

        if not piece_move_rejected and past_stack_cost_threshold:
            can_stack = self.pay_stacking_cost(user, 1)
            if not can_stack:
                logger.debug("rejecting piece move because can't pay stacking cost")
                piece_move_rejected = reject_piece_move()

        if not piece_move_rejected:
            reset_stacked_ids.difference_update(stacked_piece_ids)
            self.update_stack_status(puzzle, reset_stacked_ids, stacked=False)
            self.update_stack_status(puzzle, stacked_piece_ids, stacked=True)
            self.publish_piece_status_update(reset_stacked_ids, stacked_piece_ids)

    def update_stack_status(self, puzzle, piece_ids, stacked=True):
        if len(piece_ids) == 0:
            return
        if stacked:
            self.redis_connection.sadd(
                "pcstacked:{puzzle}".format(puzzle=puzzle),
                *piece_ids,
            )
        else:
            self.redis_connection.srem(
                "pcstacked:{puzzle}".format(puzzle=puzzle),
                *piece_ids,
            )

    def publish_piece_status_update(self, reset_stacked_ids, stacked_piece_ids):
        """
        Publish the stacked status change so the piece can have the border
        around it be removed or added.
        """
        lines = []
        msg = ""
        for piece in reset_stacked_ids:
            lines.append(formatPieceMovementString(piece, s="0"))
        for piece in stacked_piece_ids:
            lines.append(formatPieceMovementString(piece, s="2"))
        msg = "\n".join(lines)
        r = requests.post(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/{puzzle_id}/publish_move/".format(
                HOSTAPI=self.config["HOSTAPI"],
                PORTAPI=self.config["PORTAPI"],
                puzzle_id=self.puzzle_data["puzzle_id"],
            ),
            json={"msg": msg},
        )
        if r.status_code != 200:
            logger.warning(
                "Internal puzzle api error. Could not publish pieces move to update stack status on pieces"
            )

    def reassess_all(self):
        "Update the stack status for all pieces"
        # TODO This is not optimal for larger puzzles.
        puzzle = self.puzzle_data["id"]
        stacked_piece_ids = set()
        reset_stacked_ids = set()
        pcfixed = set(map(int, self.redis_connection.smembers(f"pcfixed:{puzzle}")))

        for piece, piece_property in self.piece_properties.items():
            x = piece_property["x"]
            y = piece_property["y"]
            w = piece_property["w"]
            h = piece_property["h"]
            piece_bbox = (
                x,
                y,
                x + w,
                y + h,
            )
            piece_group = int(
                self.redis_connection.hget(f"pc:{puzzle}:{piece}", "g") or piece
            )
            pcg = set(
                map(int, self.redis_connection.smembers(f"pcg:{puzzle}:{piece_group}"))
            )

            # Reassess stacked pieces that are now intersecting with the piece after
            # it moved.
            reset_stacked_ids.add(piece)
            target_stack_counts = self.get_stack_counts(
                piece_bbox, ignore_piece_ids=pcfixed
            )
            for piece_id, stack_count in target_stack_counts.items():
                if piece_id in pcg:
                    continue
                if stack_count > GROUP_STACK_THRESHOLD:
                    stacked_piece_ids.add(piece_id)

        reset_stacked_ids.difference_update(stacked_piece_ids)
        self.update_stack_status(puzzle, reset_stacked_ids, stacked=False)
        self.update_stack_status(puzzle, stacked_piece_ids, stacked=True)
        self.publish_piece_status_update(reset_stacked_ids, stacked_piece_ids)

    def batch_process(self, puzzle, pieces):
        "Update the piece bboxes for all pieces that moved in a group"
        stacked_piece_ids = set()
        reset_stacked_ids = set()
        pcfixed = set(map(int, self.redis_connection.smembers(f"pcfixed:{puzzle}")))
        (_, first_piece_id, _, _) = pieces[0]
        piece_group = int(
            self.redis_connection.hget(f"pc:{puzzle}:{first_piece_id}", "g")
            or first_piece_id
        )
        pcg = set(
            map(int, self.redis_connection.smembers(f"pcg:{puzzle}:{piece_group}"))
        )

        for pc in pieces:
            (user, piece, x, y) = pc
            w = self.piece_properties[piece]["w"]
            h = self.piece_properties[piece]["h"]

            piece_bbox = (
                x,
                y,
                x + w,
                y + h,
            )

            # Reassess stacked pieces that were intersecting with the piece origin
            reset_stacked_ids.add(piece)
            origin_piece_bbox = self.internal_origin_bboxes[piece]
            self.move_piece(piece, piece_bbox)
            origin_stack_counts = self.get_stack_counts(
                origin_piece_bbox, ignore_piece_ids=pcfixed
            )
            for piece_id, stack_count in origin_stack_counts.items():
                if piece_id == piece:
                    reset_stacked_ids.add(piece_id)
                elif stack_count <= GROUP_STACK_THRESHOLD:
                    reset_stacked_ids.add(piece_id)

            # Reassess stacked pieces that are now intersecting with the piece after
            # it moved.
            target_stack_counts = self.get_stack_counts(
                piece_bbox, ignore_piece_ids=pcfixed
            )
            for piece_id, stack_count in target_stack_counts.items():
                if piece_id in pcg:
                    continue
                if stack_count > GROUP_STACK_THRESHOLD:
                    stacked_piece_ids.add(piece_id)

        reset_stacked_ids.difference_update(stacked_piece_ids)
        self.update_stack_status(puzzle, reset_stacked_ids, stacked=False)
        self.update_stack_status(puzzle, stacked_piece_ids, stacked=True)
        self.publish_piece_status_update(reset_stacked_ids, stacked_piece_ids)

    def move_piece(self, piece, piece_bbox):
        """
        Update location of piece by first deleting it from the rtree index and
        then inserting it in the new location.
        """
        # Delete all potential duplicates of this piece
        origin_piece_bbox = self.internal_origin_bboxes[piece]
        self.proximity_idx.delete(piece, origin_piece_bbox)
        # TODO: probably no need to double tap here now since the origin piece
        # bbox is tracked internally.
        # for item in list(self.proximity_idx.intersection(origin_piece_bbox, objects=True)):
        #     if item.id == piece:
        #         logger.error(f"Found and deleted {piece} at {item.bbox}")
        #         self.proximity_idx.delete(piece, item.bbox)

        self.proximity_idx.insert(piece, piece_bbox)
        self.internal_origin_bboxes[piece] = piece_bbox

    def get_stack_counts(self, bbox, ignore_piece_ids={}):
        "With each intersecting bbox; reassess the stack count of other bboxes that intersect it."
        result = {}
        hits = list(self.proximity_idx.intersection(bbox, objects=True))
        for item in hits:
            intersecting_hits = self.proximity_idx.intersection(item.bbox, objects=True)
            # stack_count = 0
            overlapping_ids = set()
            coverage = get_bbox_area(item.bbox)
            adjacent_piece_ids = set(self.piece_properties[item.id]["adjacent"].keys())
            for intersecting_item in intersecting_hits:
                if intersecting_item.id in adjacent_piece_ids:
                    continue
                if intersecting_item.id in ignore_piece_ids:
                    continue
                intersecting_bbox = (
                    max(item.bbox[0], intersecting_item.bbox[0]),
                    max(item.bbox[1], intersecting_item.bbox[1]),
                    min(item.bbox[2], intersecting_item.bbox[2]),
                    min(item.bbox[3], intersecting_item.bbox[3]),
                )
                intersecting_coverage = get_bbox_area(intersecting_bbox)
                percent_of_item_is_covered_by_bbox = intersecting_coverage / coverage

                if percent_of_item_is_covered_by_bbox >= OVERLAP_THRESHOLD:
                    # stack_count = stack_count + 1
                    overlapping_ids.add(intersecting_item.id)
                # if stack_count != len(overlapping_ids):
                #     logger.debug(f"duplicates? {stack_count} != {overlapping_ids}")
                result[item.id] = len(overlapping_ids)
        # logger.debug(result)
        return result

    def pay_stacking_cost(self, user, amount):
        can_stack = False
        points_key = f"points:{user}"
        recent_points = int(self.redis_connection.get(points_key) or "0")

        if recent_points > amount:
            self.redis_connection.decr(points_key, amount=amount)
            can_stack = True
        else:
            can_stack = False
        return can_stack

        # Not updating karma points and publishing since don't have ip here and
        # would need to send a request to the api in order to publish on sse.
        # karma_key = f"karma:{puzzle}:{ip}"
        # # Extend the karma points expiration since it has changed
        # self.redis_connection.expire(
        #     karma_key, self.config["KARMA_POINTS_EXPIRE"]
        # )
        # karma = self.redis_connection.decr(karma_key)
        # karma_change = -1

        # if karma_change and user != ANONYMOUS_USER_ID:
        #     sse.publish(
        #         "{user}:{piece}:{karma}:{karma_change}".format(
        #             user=user,
        #             piece=piece,
        #             karma=karma + recent_points,
        #             karma_change=karma_change,
        #         ),
        #         type="karma",
        #         channel="puzzle:{puzzle_id}".format(puzzle_id=puzzleData["puzzle_id"]),
        #     )
