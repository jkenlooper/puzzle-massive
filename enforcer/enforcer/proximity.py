import time
import logging

import requests

from api.tools import formatPieceMovementString

logger = logging.getLogger(__name__)

# TODO: make these configurable in the site.cfg, they could also be configurable
# per puzzle.
STACK_THRESHOLD = 3
STACK_LIMIT = 6
OVERLAP_THRESHOLD = 0.3


def get_bbox_area(bbox):
    return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])


class Proximity:
    """
    Count the pieces in proximity on the piece that moved.

    Piece proximity threshold is based on count of adjacent pieces.
    """

    def __init__(
        self, redis_connection, proximity_idx, puzzle_data, piece_properties, config
    ):
        self.config = config
        logger.setLevel(logging.DEBUG if config["DEBUG"] else logging.INFO)
        self.redis_connection = redis_connection
        self.proximity_idx = proximity_idx
        self.piece_properties = piece_properties
        self.puzzle_data = puzzle_data
        self.proximity_init_time = time.time()

    def process(self, user, puzzle, piece, origin_x, origin_y, x, y):
        # rotate is not implemented yet; leaving origin_r as 0 for now.
        stacked_piece_ids = set()
        reset_stacked_ids = set()
        reject_piece_move = False
        origin_r = 0
        logger.debug(
            f"proximity process {user}, {puzzle}, {piece}, {origin_x}, {origin_y}, {x}, {y}"
        )
        w = self.piece_properties[piece]["w"]
        h = self.piece_properties[piece]["h"]
        origin_piece_bbox = [
            origin_x,
            origin_y,
            origin_x + w,
            origin_y + h,
        ]
        piece_bbox = [
            x,
            y,
            x + w,
            y + h,
        ]
        pcfixed = set(
            map(int, self.redis_connection.smembers(f"pcfixed:{puzzle}"))
        )

        # Reassess stacked pieces that were intersecting with the piece before
        # it moved.
        origin_stack_counts = self.get_stack_counts(origin_piece_bbox, pcfixed=pcfixed)
        for piece_id, stack_count in origin_stack_counts.items():
            if piece_id == piece:
                reset_stacked_ids.add(piece_id)
            elif stack_count <= STACK_THRESHOLD:
                reset_stacked_ids.add(piece_id)

        self.move_piece(piece, origin_piece_bbox, piece_bbox)

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
                self.move_piece(piece, piece_bbox, origin_piece_bbox)
                success = True
            return success

        # Reassess stacked pieces that are now intersecting with the piece after
        # it moved.
        piece_move_rejected = False
        target_stack_counts = self.get_stack_counts(piece_bbox, pcfixed=pcfixed)
        for piece_id, stack_count in target_stack_counts.items():
            if stack_count > STACK_LIMIT:
                piece_move_rejected = reject_piece_move()
                break
            if piece_id in pcfixed:
                continue
            if stack_count > STACK_THRESHOLD:
                try:
                    reset_stacked_ids.remove(piece_id)
                except KeyError:
                    pass
                stacked_piece_ids.add(piece_id)

        if not piece_move_rejected:
            reset_stacked_ids.difference_update(stacked_piece_ids)
            self.update_stack_status(puzzle, reset_stacked_ids, stacked=False)
            self.update_stack_status(puzzle, stacked_piece_ids, stacked=True)
            self.publish_piece_status_update(reset_stacked_ids, stacked_piece_ids)
        #pcstacked = set(
        #    map(int, self.redis_connection.smembers(f"pcstacked:{puzzle}"))
        #)
        #logger.debug(f"stacked: {pcstacked}")

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
        logger.debug(msg)
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

    def batch_process(self, puzzle, pieces):
        "Update the piece bboxes for all pieces that moved in a group"
        stacked_piece_ids = set()
        reset_stacked_ids = set()
        pcfixed = set(
            map(int, self.redis_connection.smembers(f"pcfixed:{puzzle}"))
        )
        for pc in pieces:
            (piece, origin_x, origin_y, x, y) = pc
            w = self.piece_properties[piece]["w"]
            h = self.piece_properties[piece]["h"]

            origin_piece_bbox = [
                origin_x,
                origin_y,
                origin_x + w,
                origin_y + h,
            ]
            piece_bbox = [
                x,
                y,
                x + w,
                y + h,
            ]

            # Reassess stacked pieces that were intersecting with the piece before
            # it moved.
            origin_stack_counts = self.get_stack_counts(origin_piece_bbox, pcfixed=pcfixed)
            for piece_id, stack_count in origin_stack_counts.items():
                if piece_id == piece:
                    reset_stacked_ids.add(piece_id)
                elif stack_count <= STACK_THRESHOLD:
                    reset_stacked_ids.add(piece_id)

            self.move_piece(piece, origin_piece_bbox, piece_bbox)

            # Reassess stacked pieces that are now intersecting with the piece after
            # it moved.
            target_stack_counts = self.get_stack_counts(piece_bbox, pcfixed=pcfixed)
            for piece_id, stack_count in target_stack_counts.items():
                if piece_id in pcfixed:
                    continue
                if stack_count > STACK_THRESHOLD:
                    try:
                        reset_stacked_ids.remove(piece_id)
                    except KeyError:
                        pass
                    stacked_piece_ids.add(piece_id)

        reset_stacked_ids.difference_update(stacked_piece_ids)
        self.update_stack_status(puzzle, reset_stacked_ids, stacked=False)
        self.update_stack_status(puzzle, stacked_piece_ids, stacked=True)
        self.publish_piece_status_update(reset_stacked_ids, stacked_piece_ids)

    def move_piece(self, piece, origin_piece_bbox, piece_bbox):
        """
        Update location of piece by first deleting it from the rtree index and
        then inserting it in the new location.
        """
        self.proximity_idx.delete(piece, origin_piece_bbox)
        self.proximity_idx.insert(piece, piece_bbox)

    def get_stack_counts(self, bbox, pcfixed={}):
        "With each intersecting bbox; reassess the stack count of other bboxes that intersect it."
        result = {}
        hits = list(self.proximity_idx.intersection(bbox, objects=True))
        for item in hits:
            intersecting_hits = self.proximity_idx.intersection(item.bbox, objects=True)
            stack_count = 0
            coverage = get_bbox_area(item.bbox)
            adjacent_piece_ids = set(self.piece_properties[item.id]["adjacent"].keys())
            for intersecting_item in intersecting_hits:
                if intersecting_item.id in adjacent_piece_ids:
                    continue
                if intersecting_item.id in pcfixed:
                    continue
                intersecting_bbox = [
                    max(item.bbox[0], intersecting_item.bbox[0]),
                    max(item.bbox[1], intersecting_item.bbox[1]),
                    min(item.bbox[2], intersecting_item.bbox[2]),
                    min(item.bbox[3], intersecting_item.bbox[3]),
                ]
                intersecting_coverage = get_bbox_area(intersecting_bbox)
                percent_of_item_is_covered_by_bbox = (intersecting_coverage / coverage)

                if percent_of_item_is_covered_by_bbox >= OVERLAP_THRESHOLD:
                    stack_count = stack_count + 1
                result[item.id] = stack_count
        return result
