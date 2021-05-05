import time
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# record origin of the piece
# origin of piece is packed in the token
# count pieces that are overlapping
# if stacked
# use internal request to update piece and other pieces
# that are overlapping statuses to stacked
# if stacked and past stack limit
# reject piece move
# put request back to origin
# use internal only request to move piece back to origin


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
        piece_padded_bbox = [
            max(x - self.piece_padding, 0),
            max(y - self.piece_padding, 0),
            x + self.piece_padding + w,
            y + self.piece_padding + h,
        ]
        self.move_piece(piece, origin_piece_bbox, piece_bbox)

        proximity_count = self.proximity_idx.count(piece_padded_bbox)
        logger.debug(f"proximity count {proximity_count}")

    def batch_process(self, pieces):
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
            # TODO: WIP

    def move_piece(self, piece, origin_piece_bbox, piece_bbox):
        """
        Update location of piece by first deleting it from the rtree index and
        then inserting it in the new location.
        """
        self.proximity_idx.delete(piece, origin_piece_bbox)
        self.proximity_idx.insert(piece, piece_bbox)
