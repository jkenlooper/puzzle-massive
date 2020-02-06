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
        self.puzzle_mutation_id = int(
            self.redis_connection.get(self.pzm_puzzle_key) or "0"
        )
        self.watched_keys.add(self.pzm_puzzle_key)

        self.pc_puzzle_piece_key = "pc:{puzzle}:{piece}".format(
            puzzle=puzzle, piece=piece
        )

        self.origin_x = None
        self.origin_y = None
        self.origin_r = None

        self.piece_properties = None
        self.adjacent_piece_properties = None

        # group_id: count of pieces in that group
        self.adjacent_piece_group_counts = {}

        self.pieces_in_proximity_to_target = set()
        self.grouped_piece_properties = None

    def start(self):
        ""

        self._load_related_pieces()
        if len(self.pieces_in_proximity_to_target) >= 4:
            self._stack_pieces()

        else:
            self._join_pieces()

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
            current_puzzle_mutation_id = int(pipe.get(self.pzm_puzzle_key) or "0")
            if current_puzzle_mutation_id != self.puzzle_mutation_id:
                raise PieceMutateError

            self.piece_properties = self._int_piece_properties(
                pipe.hgetall(self.pc_puzzle_piece_key)
            )
            adjacent_pieces_list = self._get_adjacent_pieces_list(self.piece_properties)

            # Put back to buffered mode since the watch was called.
            pipe.multi()

            pcg_puzzle_g_key = "pcg:{puzzle}:{piece_group}".format(
                puzzle=self.puzzle, piece_group=self.piece_properties.get("g")
            )
            self.origin_x = self.piece_properties.get("x")
            self.origin_y = self.piece_properties.get("y")
            self.origin_r = self.piece_properties.get("r")

            tolerance = int(100 / 2)

            # pcx_puzzle
            pipe.zrangebyscore(
                "pcx:{puzzle}".format(puzzle=self.puzzle),
                self.target_x - tolerance,
                self.target_x + tolerance,
            )
            # pcy_puzzle
            pipe.zrangebyscore(
                "pcy:{puzzle}".format(puzzle=self.puzzle),
                self.target_y - tolerance,
                self.target_y + tolerance,
            )
            # pcfixed_puzzle
            pipe.smembers("pcfixed:{puzzle}".format(puzzle=self.puzzle))
            # pcg_puzzle_g
            pipe.smembers(pcg_puzzle_g_key)

            # pc_puzzle_adjacent_piece_properties
            for adjacent_piece in adjacent_pieces_list:
                pc_puzzle_adjacent_piece_key = "pc:{puzzle}:{adjacent_piece}".format(
                    puzzle=self.puzzle, adjacent_piece=adjacent_piece
                )
                pipe.hgetall(pc_puzzle_adjacent_piece_key)
                self.watched_keys.add(pc_puzzle_adjacent_piece_key)

            # pcg_puzzle_piece_group_count =countOfPiecesInPieceGroup
            pipe.scard(
                "pcg:{puzzle}:{g}".format(
                    puzzle=self.puzzle, g=self.piece_properties.get("g", self.piece)
                )
            )

            phase_1_response = pipe.execute()
            (
                pcx_puzzle,
                pcy_puzzle,
                pcfixed_puzzle,
                pcg_puzzle_g,
                pc_puzzle_adjacent_piece_properties,
                pcg_puzzle_piece_group_count,
            ) = (
                phase_1_response[0],
                phase_1_response[1],
                phase_1_response[2],
                phase_1_response[3],
                phase_1_response[4 : 4 + len(adjacent_pieces_list)],
                phase_1_response[4 + len(adjacent_pieces_list)],
            )
            pcx_puzzle = set(map(int, pcx_puzzle))
            pcy_puzzle = set(map(int, pcy_puzzle))
            pcfixed_puzzle = set(map(int, pcfixed_puzzle))
            pcg_puzzle_g = set(map(int, pcg_puzzle_g))
            self.all_other_pieces_in_piece_group = pcg_puzzle_g.copy()
            self.all_other_pieces_in_piece_group.discard(self.piece)
            pc_puzzle_adjacent_piece_properties = map(
                self._int_piece_properties, pc_puzzle_adjacent_piece_properties
            )

            self.pieces_in_proximity_to_target = self._get_pieces_in_proximity_to_target(
                pcx_puzzle, pcy_puzzle, pcfixed_puzzle, pcg_puzzle_g
            )
            # Get Adjacent Piece Properties
            self.adjacent_piece_properties = dict(
                list(zip(adjacent_pieces_list, pc_puzzle_adjacent_piece_properties))
            )
            self.adjacent_piece_group_ids = self._get_adjacent_piece_group_ids(
                self.adjacent_piece_properties
            )

        ## pipeline phase 2
        # grouped pieces
        self.watched_keys.add(pcg_puzzle_g_key)
        with self.redis_connection.pipeline(transaction=True) as pipe:
            pipe.watch(*self.watched_keys)

            # Raise an error if the puzzle pieces have changed since phase 1 started.
            current_puzzle_mutation_id = int(pipe.get(self.pzm_puzzle_key) or "0")
            if current_puzzle_mutation_id != self.puzzle_mutation_id:
                raise PieceMutateError

            # Put back to buffered mode since the watch was called.
            pipe.multi()

            # updateGroupedPiecesPositions groupedPiecesXY
            # pc_puzzle_grouped_pieces
            grouped_piece_property_list = ["x", "y", "r", "g", "s"]
            for grouped_piece in self.all_other_pieces_in_piece_group:
                pc_puzzle_grouped_piece_key = "pc:{puzzle}:{grouped_piece}".format(
                    puzzle=self.puzzle, grouped_piece=grouped_piece
                )
                pipe.hmget(
                    pc_puzzle_grouped_piece_key, grouped_piece_property_list,
                )
                self.watched_keys.add(pc_puzzle_grouped_piece_key)

            # pcg_puzzle_piece_adjacent_group_counts
            # for adjacent_piece_group
            adjacent_group_list = list(set(self.adjacent_piece_group_ids.values()))
            for adjacent_group in adjacent_group_list:
                pcg_puzzle_adjacent_group_count_key = "pcg:{puzzle}:{g}".format(
                    puzzle=self.puzzle, g=adjacent_group
                )
                pipe.scard(pcg_puzzle_adjacent_group_count_key)

            phase_2_response = pipe.execute()
            (pc_puzzle_grouped_pieces, pcg_puzzle_piece_adjacent_group_counts) = (
                phase_2_response[: len(self.all_other_pieces_in_piece_group)],
                phase_2_response[
                    len(self.all_other_pieces_in_piece_group) : len(
                        self.all_other_pieces_in_piece_group
                    )
                    + len(adjacent_group_list)
                ],
            )
            pc_puzzle_grouped_pieces = list(
                map(
                    self._int_piece_properties,
                    map(
                        lambda x: dict(list(zip(grouped_piece_property_list, x))),
                        pc_puzzle_grouped_pieces,
                    ),
                )
            )
            self.adjacent_piece_group_counts = dict(
                list(zip(adjacent_group_list, pcg_puzzle_piece_adjacent_group_counts))
            )

            # groupedPiecesXY plus g and s
            self.grouped_piece_properties = dict(
                list(
                    zip(self.all_other_pieces_in_piece_group, pc_puzzle_grouped_pieces)
                )
            )
            print(self.grouped_piece_properties)

    def _stack_pieces(self):
        "When too many pieces are within proximity to each other, skip trying to join any of them and mark them as stacked"

    def _join_pieces(self):
        # reset pcstacked and pc s status to not stacked for all pieces in
        # proximity

        # TODO: Determine if the piece joins any other pieces

        with self.redis_connection.pipeline(transaction=True) as pipe:
            pipe.watch(*self.watched_keys)

            # Raise an error if the puzzle pieces have changed since phase 1 started.
            current_puzzle_mutation_id = int(pipe.get(self.pzm_puzzle_key) or "0")
            if current_puzzle_mutation_id != self.puzzle_mutation_id:
                raise PieceMutateError

            # Put back to buffered mode since the watch was called.
            pipe.multi()

            # TODO: update the piece and it's piece group

            # Bump the pzm id when done mutating the puzzle on the last phase.
            pipe.incr(self.pzm_puzzle_key)

            pipe.execute()

    def _get_pieces_in_proximity_to_target(
        self, pcx_puzzle, pcy_puzzle, pcfixed_puzzle, pcg_puzzle_g
    ):
        "Pieces in proximity to target"
        # TODO:  This is only using the x and y coordinates and not the actual
        # piece footprint. If custom piece shapes are used that have different
        # widths and heights, then a different method will need to be used.
        pieces_in_proximity_to_target = set.intersection(
            set(pcx_puzzle), set(pcy_puzzle)
        )
        # Remove immovable pieces from the pieces in proximity
        if len(pieces_in_proximity_to_target) > 0:
            pieces_in_proximity_to_target = pieces_in_proximity_to_target.difference(
                pcfixed_puzzle
            )
        # Remove pieces own group from the pieces in proximity
        if len(pieces_in_proximity_to_target) > 0:
            pieces_in_proximity_to_target = pieces_in_proximity_to_target.difference(
                pcg_puzzle_g
            )
        pieces_in_proximity_to_target.add(self.piece)
        return pieces_in_proximity_to_target

    def _get_adjacent_pieces_list(self, piece_properties):
        "Get adjacent pieces list"
        return list(
            map(
                int,
                [
                    x
                    for x in list(piece_properties.keys())
                    if x not in ("x", "y", "r", "w", "h", "b", "rotate", "g", "s")
                ],
            )
        )

    def _int_piece_properties(self, piece_properties):
        ""
        int_props = ("x", "y", "r", "w", "h", "rotate", "g")
        for (k, v) in piece_properties.items():
            if k in int_props:
                piece_properties[k] = int(v)

        return piece_properties

    def _get_adjacent_piece_group_ids(self, adjacent_piece_properties):
        "Return a dict of adjacent piece id to the group id when group id is not None."
        adjacent_piece_group_ids = dict()
        for (piece_id, prop) in adjacent_piece_properties.items():
            if prop.get("g") != None:
                adjacent_piece_group_ids[piece_id] = prop.get("g")
        return adjacent_piece_group_ids
