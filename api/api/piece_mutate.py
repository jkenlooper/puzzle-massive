class PieceMutateError(Exception):
    """
    Error with piece mutatation.
    """


class PieceGroupConflictError(PieceMutateError):
    """
    When some piece data from redis has changed after the process to update
    piece groups has happened.
    """


class PieceMutateProcess:
    ""

    def __init__(self, redis_connection, puzzle, piece, target_x, target_y, target_r):
        ""
        self.redis_connection = redis_connection
        self.puzzle = puzzle
        self.piece = piece
        self.target_x = target_x
        self.target_y = target_y
        self.target_r = target_r

        self.watched_keys = set()

        self.pzm_puzzle_key = "pzm:{puzzle}".format(puzzle=puzzle)
        self.puzzle_mutation_id = self.redis_connection.incr(self.pzm_puzzle_key)
        self.watched_keys.add(self.pzm_puzzle_key)

        self.pc_puzzle_piece_key = "pc:{puzzle}:{piece}".format(
            puzzle=puzzle, piece=piece
        )

        self.origin_x = None
        self.origin_y = None
        self.origin_r = None

        self.piece_properties = None
        self.pieces_in_proximity_to_target = set()
        self.grouped_pieces_x_y = None

    def start(self):
        ""

        self._load_related_pieces()

        # create pipeline
        # watch the watched keys
        # set new piece mutations in a single transaction.

    def _load_related_pieces(self):
        """
        get all piece details and associated pieces.
        add to watched keys
        """
        self.watched_keys.add(self.pc_puzzle_piece_key)

        ## pipeline phase 1
        with self.redis_connection.pipeline(transaction=True) as pipe:
            pipe.watch(*self.watched_keys)

            # Raise an error if the puzzle pieces have changed since phase 1 started.
            current_puzzle_mutation_id = int(pipe.get(self.pzm_puzzle_key))
            if current_puzzle_mutation_id != self.puzzle_mutation_id:
                raise PieceMutateError

            self.piece_properties = pipe.hgetall(self.pc_puzzle_piece_key)

            # Put back to buffered mode since the watch was called.
            pipe.multi()

            pcg_puzzle_g_key = "pcg:{puzzle}:{piece_group}".format(
                puzzle=self.puzzle, piece_group=self.piece_properties.get("g")
            )
            self.origin_x = int(self.piece_properties.get("x"))
            self.origin_y = int(self.piece_properties.get("y"))
            self.origin_r = int(self.piece_properties.get("r"))

            tolerance = int(100 / 2)
            pipe.zrangebyscore(
                "pcx:{puzzle}".format(puzzle=self.puzzle),
                self.target_x - tolerance,
                self.target_x + tolerance,
            )
            pipe.zrangebyscore(
                "pcy:{puzzle}".format(puzzle=self.puzzle),
                self.target_y - tolerance,
                self.target_y + tolerance,
            )
            pipe.smembers("pcfixed:{puzzle}".format(puzzle=self.puzzle))

            pipe.smembers(pcg_puzzle_g_key)

            (pcx_puzzle, pcy_puzzle, pcfixed_puzzle, pcg_puzzle_g) = pipe.execute()

        ## pipeline phase 2
        # grouped pieces
        self.watched_keys.add(pcg_puzzle_g_key)
        with self.redis_connection.pipeline(transaction=True) as pipe:
            pipe.watch(*self.watched_keys)

            # Raise an error if the puzzle pieces have changed since phase 1 started.
            current_puzzle_mutation_id = int(pipe.get(self.pzm_puzzle_key))
            if current_puzzle_mutation_id != self.puzzle_mutation_id:
                raise PieceMutateError

            # Put back to buffered mode since the watch was called.
            pipe.multi()

            # Pieces in proximity to target
            self.pieces_in_proximity_to_target = set.intersection(
                set(pcx_puzzle), set(pcy_puzzle)
            )
            # Remove immovable pieces from the pieces in proximity
            if len(self.pieces_in_proximity_to_target) > 0:
                immovable_pieces = set(map(int, pcfixed_puzzle))
                self.pieces_in_proximity_to_target = self.pieces_in_proximity_to_target.difference(
                    immovable_pieces
                )
            # Remove pieces own group from the pieces in proximity
            if len(self.pieces_in_proximity_to_target) > 0:
                grouped_pieces = set(map(int, pcg_puzzle_g))
                self.pieces_in_proximity_to_target = self.pieces_in_proximity_to_target.difference(
                    grouped_pieces
                )
            self.pieces_in_proximity_to_target.add(self.piece)

            # updateGroupedPiecesPositions groupedPiecesXY
            # allOtherPiecesInPieceGroup is same as pcg_puzzle_g
            all_other_pieces_in_piece_group = pcg_puzzle_g.copy()
            # print(all_other_pieces_in_piece_group)
            if len(all_other_pieces_in_piece_group) > 0:
                # TODO: why piece is str here?
                all_other_pieces_in_piece_group.remove(str(self.piece))
                for grouped_piece in all_other_pieces_in_piece_group:
                    pc_puzzle_grouped_piece_key = "pc:{puzzle}:{grouped_piece}".format(
                        puzzle=self.puzzle, grouped_piece=grouped_piece
                    )
                    pipe.hmget(
                        pc_puzzle_grouped_piece_key, ["x", "y"],
                    )
                    self.watched_keys.add(pc_puzzle_grouped_piece_key)

            phase_2_response = pipe.execute()
            (pc_puzzle_grouped_pieces,) = (
                phase_2_response[: len(all_other_pieces_in_piece_group)],
            )
            # groupedPiecesXY
            self.grouped_pieces_x_y = dict(
                list(zip(all_other_pieces_in_piece_group, pc_puzzle_grouped_pieces))
            )

        # adjacent pieces

        # Get the puzzle piece origin position
        # (originX, originY) = list(
        #    map(int, redis_connection.hmget(pc_puzzle_piece_key, ["x", "y"]),)
        # )
