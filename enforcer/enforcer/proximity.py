import time
import logging
from math import ceil


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# record origin of the piece
#   origin of piece is packed in the token
# count pieces that are overlapping
# if stacked
#   use internal request to update piece and other pieces
#   that are overlapping statuses to stacked
# if stacked and past stack limit
#   reject piece move
#   put request back to origin
#   use internal only request to move piece back to origin
# if not stacked
#   update pcstacked status
#   delete stacked status (s)

# TODO: make these configurable in the site.cfg
STACK_THRESHOLD = 4
STACK_LIMIT = 10


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
        piece_properties,
        piece_join_tolerance=100,
    ):
        self.redis_connection = redis_connection
        self.proximity_idx = proximity_idx
        self.piece_properties = piece_properties
        self.proximity_init_time = time.time()
        self.piece_padding = int(piece_join_tolerance * 0.5)

    def process(self, user, puzzle, piece, origin_x, origin_y, x, y):
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
        piece_padded_bbox = [
            max(x - self.piece_padding, 0),
            max(y - self.piece_padding, 0),
            x + self.piece_padding + w,
            y + self.piece_padding + h,
        ]
        self.move_piece(piece, origin_piece_bbox, piece_bbox)

        adjacent_piece_ids = set(self.piece_properties[piece]["adjacent"].keys())
        proximity_count = self.proximity_idx.count(piece_padded_bbox) - 1
        if proximity_count == 0:
            return

        hits = list(self.proximity_idx.intersection(piece_padded_bbox, objects=True))
        proximity_count = len(hits)
        stacked_piece_ids = set()
        reset_stacked_ids = set()
        reject_piece_move = False
        # TODO: Should immovable pieces be counted or not?
        ignore_immovable_pieces = True
        pcstacked = set(map(int, self.redis_connection.smembers(f"pcstacked:{puzzle}")))
        logger.debug(f"all pcstacked {pcstacked}")

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
                # this item's bbox and the piece_padded_bbox.
                intersecting_bbox = [
                    max(piece_padded_bbox[0], item.bbox[0]),
                    max(piece_padded_bbox[1], item.bbox[1]),
                    min(piece_padded_bbox[2], item.bbox[2]),
                    min(piece_padded_bbox[3], item.bbox[3]),
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
            logger.debug(
                f"TODO: Set these piece ids to stacked status: {stacked_piece_ids}"
            )
            # TODO: send internal request to update stacked status for stacked_piece_ids
            # The update to stacked piece status should only be done for pieces
            # that are not in the immovable status.
            # OR modify the pcstacked and s directly?
        if reject_piece_move:
            logger.debug(f"TODO: Exceeded stack limit; reject piece move for {piece}")
            # TODO: send internal request to reject piece move
        if len(reset_stacked_ids) > 0:
            logger.debug(f"TODO: Reset stacked pieces: {stacked_piece_ids}")

        logger.debug(f"proximity count {proximity_count}")
        logger.debug(f"adjacent count {len(self.piece_properties[piece]['adjacent'])}")

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
            # TODO: update the pcstacked and s status on all pieces moved in the group?

    def move_piece(self, piece, origin_piece_bbox, piece_bbox):
        """
        Update location of piece by first deleting it from the rtree index and
        then inserting it in the new location.
        """
        self.proximity_idx.delete(piece, origin_piece_bbox)
        self.proximity_idx.insert(piece, piece_bbox)
