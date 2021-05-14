import time
import logging
from math import ceil

import requests

logger = logging.getLogger(__name__)

# TODO: make these configurable in the site.cfg, they could also be configurable
# per puzzle.
STACK_THRESHOLD = 3
STACK_LIMIT = 4


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
        piece_bbox_coverage = get_bbox_area(piece_bbox)
        self.move_piece(piece, origin_piece_bbox, piece_bbox)

        adjacent_piece_ids = set(self.piece_properties[piece]["adjacent"].keys())
        proximity_count = self.proximity_idx.count(piece_bbox) - 1
        if proximity_count == 0:
            self.update_stack_status(puzzle, [piece], stacked=False)
            return

        hits = list(self.proximity_idx.intersection(piece_bbox, objects=True))
        proximity_count = len(hits)
        stacked_piece_ids = set()
        reset_stacked_ids = set()
        reject_piece_move = False
        # TODO: Should immovable pieces be counted or not?
        ignore_immovable_pieces = True
        pcstacked = set(map(int, self.redis_connection.smembers(f"pcstacked:{puzzle}")))

        if proximity_count > STACK_THRESHOLD:
            if ignore_immovable_pieces:
                pcfixed = set(
                    map(int, self.redis_connection.smembers(f"pcfixed:{puzzle}"))
                )
            for item in hits:
                if item.id == piece:
                    continue
                if item.id in adjacent_piece_ids:
                    # don't count the pieces that can join this piece
                    continue
                # count how many pieces are overlapping for the intersection of
                # this item's bbox and the piece_bbox.
                intersecting_bbox = [
                    max(piece_bbox[0], item.bbox[0]),
                    max(piece_bbox[1], item.bbox[1]),
                    min(piece_bbox[2], item.bbox[2]),
                    min(piece_bbox[3], item.bbox[3]),
                ]
                intersecting_bbox_coverage = get_bbox_area(intersecting_bbox)
                intersecting_hits = list(
                    self.proximity_idx.intersection(intersecting_bbox, objects=True)
                )
                intersecting_count = len(intersecting_hits) - 1
                if intersecting_count < ceil(
                    STACK_THRESHOLD * (intersecting_bbox_coverage / piece_bbox_coverage)
                ):
                    reset_stacked_ids.update(
                        set(map(lambda x: x.id, intersecting_hits))
                    )
                    continue
                intersecting_stacked_piece_ids = set()
                intersecting_adjacent_piece_ids = set()
                for intersecting_item in intersecting_hits:
                    if intersecting_item.id == item.id:
                        continue
                    if intersecting_item.id in adjacent_piece_ids:
                        # don't count the pieces that can join this piece
                        intersecting_adjacent_piece_ids.add(intersecting_item.id)
                        continue
                    if ignore_immovable_pieces and intersecting_item.id in pcfixed:
                        # don't count pieces that are immovable since updating
                        # the status from immovable to fixed would break things.
                        continue
                    intersecting_stacked_piece_ids.add(intersecting_item.id)
                if len(intersecting_stacked_piece_ids) <= STACK_THRESHOLD:
                    reset_stacked_ids.update(intersecting_stacked_piece_ids)
                    reset_stacked_ids.update(intersecting_adjacent_piece_ids)
                    reset_stacked_ids.add(item.id)
                if len(intersecting_stacked_piece_ids) > STACK_THRESHOLD:
                    stacked_piece_ids.update(intersecting_stacked_piece_ids)
                if len(intersecting_stacked_piece_ids) > STACK_LIMIT:
                    reject_piece_move = True
        else:
            reset_stacked_ids.update(set(map(lambda x: x.id, hits)))

        reset_stacked_ids = reset_stacked_ids.intersection(pcstacked)
        if len(stacked_piece_ids) > 0:
            logger.debug(f"Set these piece ids to stacked status: {stacked_piece_ids}")
            self.update_stack_status(puzzle, stacked_piece_ids, stacked=True)
        if reject_piece_move:
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
        if len(reset_stacked_ids) > 0:
            logger.debug(f"Reset stacked pieces: {reset_stacked_ids}")
            self.update_stack_status(puzzle, reset_stacked_ids, stacked=False)

        logger.debug(f"proximity count {proximity_count}")
        logger.debug(f"adjacent count {len(self.piece_properties[piece]['adjacent'])}")

    def update_stack_status(self, puzzle, piece_ids, stacked=True):
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

    def batch_process(self, pieces):
        "Update the piece bboxes for all pieces that moved in a group"
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
            self.move_piece(piece, origin_piece_bbox, piece_bbox)
            # TODO: update the pcstacked and pcfixed status on all pieces moved in the group?

    def move_piece(self, piece, origin_piece_bbox, piece_bbox):
        """
        Update location of piece by first deleting it from the rtree index and
        then inserting it in the new location.
        """
        self.proximity_idx.delete(piece, origin_piece_bbox)
        self.proximity_idx.insert(piece, piece_bbox)
