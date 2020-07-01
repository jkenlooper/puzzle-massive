from api.tools import formatPieceMovementString


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

    def __init__(
        self,
        redis_connection,
        puzzle,
        piece,
        target_x,
        target_y,
        target_r,
        piece_count=0,
    ):
        ""
        self.redis_connection = redis_connection
        self.puzzle = puzzle
        self.piece = piece
        self.target_x = target_x
        self.target_y = target_y
        self.target_r = target_r
        self.piece_count = piece_count

        self.watched_keys = set()

        self.pzm_puzzle_key = "pzm:{puzzle}".format(puzzle=puzzle)
        # Bump the pzm id when preparing to mutate the puzzle.
        self.puzzle_mutation_id = self.redis_connection.incr(self.pzm_puzzle_key)
        self.redis_connection.expire(self.pzm_puzzle_key, 60)
        self.watched_keys.add(self.pzm_puzzle_key)

        self.pc_puzzle_piece_key = "pc:{puzzle}:{piece}".format(
            puzzle=puzzle, piece=piece
        )

        self.origin_x = None
        self.origin_y = None
        self.origin_r = None
        self.offset_x = None
        self.offset_y = None

        self.piece_properties = None
        self.adjacent_piece_properties = None

        # group_id: count of pieces in that group
        self.adjacent_piece_group_counts = {}

        self.pieces_in_proximity_to_target = set()
        self.grouped_piece_properties = None
        self.all_other_pieces_in_piece_group = set()

        self.can_join_adjacent_piece = None

    def start(self):
        ""

        self._load_related_pieces()

        # TODO: return early if piece move would be invalid (piece proximity,
        # etc.)

        self._set_can_join_adjacent_piece()

        msg = ""
        status = ""
        with self.redis_connection.pipeline(transaction=True) as pipe:
            pipe.watch(*self.watched_keys)

            # Raise an error if the puzzle pieces have changed since phase 1 started.
            current_puzzle_mutation_id = int(pipe.get(self.pzm_puzzle_key))
            if current_puzzle_mutation_id != self.puzzle_mutation_id:
                raise PieceMutateError("start pzm")

            # Put back to buffered mode since the watch was called.
            pipe.multi()

            # TODO: update the piece and it's piece group
            if len(self.pieces_in_proximity_to_target) >= 4:
                msg = self._stack_pieces(pipe)
                status = "stacked"
            else:
                msg = self._reset_pieces_in_proximity_stacked_status(pipe)
                if self.can_join_adjacent_piece == None:
                    msg += self._move_pieces(pipe)
                    status = "moved"
                else:
                    msg += self._join_pieces(pipe)
                    if self._puzzle_completed():
                        status = "completed"
                    else:
                        status = "joined"

            # Bump the pzm id when done mutating the puzzle on the last phase.
            pipe.incr(self.pzm_puzzle_key)

            result = pipe.execute()
            if not result:
                raise PieceMutateError("end conflict")
        return (msg, status)

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
                raise PieceMutateError("phase 1 pzm")

            self.piece_properties = self._int_piece_properties(
                pipe.hgetall(self.pc_puzzle_piece_key)
            )
            adjacent_pieces_list = self._get_adjacent_pieces_list(self.piece_properties)

            # Put back to buffered mode since the watch was called.
            pipe.multi()

            pcg_puzzle_g_key = "pcg:{puzzle}:{piece_group}".format(
                puzzle=self.puzzle,
                piece_group=self.piece_properties.get("g", self.piece),
            )
            self.origin_x = self.piece_properties.get("x")
            self.origin_y = self.piece_properties.get("y")
            self.origin_r = self.piece_properties.get("r")
            self._update_target_position(self.target_x, self.target_y)

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
            if not phase_1_response:
                raise PieceMutateError("phase 1 conflict")
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
            pc_puzzle_adjacent_piece_properties = list(
                map(self._int_piece_properties, pc_puzzle_adjacent_piece_properties)
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
            current_puzzle_mutation_id = int(pipe.get(self.pzm_puzzle_key))
            if current_puzzle_mutation_id != self.puzzle_mutation_id:
                raise PieceMutateError("phase 2 pzm")

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
            if (
                len(self.all_other_pieces_in_piece_group) or len(adjacent_group_list)
            ) and not phase_2_response:
                raise PieceMutateError("phase 2 conflict")
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

    def _update_target_position(self, x, y):
        self.target_x = x
        self.target_y = y
        self.offset_x = self.target_x - self.origin_x
        self.offset_y = self.target_y - self.origin_y

    def _set_can_join_adjacent_piece(self):
        "Determine if the piece can be joined to any of the adjacent pieces"
        tolerance = int(100 / 2)

        # Check if piece is close enough to any adjacent piece
        piece_group = self.piece_properties.get("g", None)
        for (
            adjacent_piece,
            adjacent_piece_props,
        ) in self.adjacent_piece_properties.items():
            # Skip if adjacent piece in same group
            if (
                piece_group != None
                and self.adjacent_piece_group_ids.get(adjacent_piece) == piece_group
            ):
                continue

            (offset_from_piece_x, offset_from_piece_y) = list(
                map(int, self.piece_properties.get(str(adjacent_piece)).split(","))
            )
            targetX = offset_from_piece_x + self.target_x
            targetY = offset_from_piece_y + self.target_y

            xlow = targetX - tolerance
            xhigh = targetX + tolerance

            # Skip If the adjacent piece is not within range of the targetX and targetY
            if not (
                (adjacent_piece_props["x"] > (targetX - tolerance))
                and (adjacent_piece_props["x"] < (targetX + tolerance))
            ):
                continue

            ylow = targetY - tolerance
            yhigh = targetY + tolerance
            if not (
                (adjacent_piece_props["y"] > (targetY - tolerance))
                and (adjacent_piece_props["y"] < (targetY + tolerance))
            ):
                continue

            # The piece can be joined to the adjacent piece
            self.can_join_adjacent_piece = adjacent_piece
            new_target_x = adjacent_piece_props["x"] - offset_from_piece_x
            new_target_y = adjacent_piece_props["y"] - offset_from_piece_y
            self._update_target_position(new_target_x, new_target_y)
            break

    def _stack_pieces(self, pipe):
        "When too many pieces are within proximity to each other, skip trying to join any of them and mark them as stacked"
        lines = []
        msg = ""
        pipe.sadd(
            "pcstacked:{puzzle}".format(puzzle=self.puzzle),
            *self.pieces_in_proximity_to_target
        )
        for piece_in_proximity in self.pieces_in_proximity_to_target:
            pipe.hset(
                "pc:{puzzle}:{piece_in_proximity}".format(
                    puzzle=self.puzzle, piece_in_proximity=piece_in_proximity
                ),
                "s",
                "2",
            )
            lines.append(formatPieceMovementString(piece_in_proximity, s="2"))

        # Move the piece
        pipe.hmset(
            self.pc_puzzle_piece_key, {"x": self.target_x, "y": self.target_y},
        )
        pipe.zadd(
            "pcx:{puzzle}".format(puzzle=self.puzzle), {self.piece: self.target_x}
        )
        pipe.zadd(
            "pcy:{puzzle}".format(puzzle=self.puzzle), {self.piece: self.target_y}
        )
        lines.append(
            formatPieceMovementString(
                self.piece, x=self.target_x, y=self.target_y, s="2"
            )
        )

        msg += "\n".join(lines)
        msg += "\n"

        # If the piece is grouped move the other pieces in group
        if self.piece_properties.get("g") != None:
            lines = self._update_grouped_pieces_positions(pipe)
            msg += "\n" + "\n".join(lines)
        return msg

    def _move_pieces(self, pipe):
        "Only move the piece and the other pieces in the group to the target position"
        lines = []
        msg = ""

        # Move the piece
        pipe.hmset(self.pc_puzzle_piece_key, {"x": self.target_x, "y": self.target_y})
        pipe.zadd(
            "pcx:{puzzle}".format(puzzle=self.puzzle), {self.piece: self.target_x}
        )
        pipe.zadd(
            "pcy:{puzzle}".format(puzzle=self.puzzle), {self.piece: self.target_y}
        )

        # Reset Piece Status for stacked (It's assumed that the piece being moved can't be an immovable piece)
        pipe.srem("pcstacked:{puzzle}".format(puzzle=self.puzzle), self.piece)
        pipe.hdel(
            "pc:{puzzle}:{piece}".format(puzzle=self.puzzle, piece=self.piece), "s"
        )
        lines.append(
            formatPieceMovementString(self.piece, x=self.target_x, y=self.target_y)
        )

        # If the piece is grouped move the other pieces in group
        if self.piece_properties.get("g") != None:
            lines.extend(self._update_grouped_pieces_positions(pipe))
        msg += "\n" + "\n".join(lines)
        return msg

    def _join_pieces(self, pipe):
        "Join the piece and the pieces group to the adjacent piece merging the two piece groups together."
        lines = []
        msg = ""
        adjacent_piece_props = self.adjacent_piece_properties.get(
            self.can_join_adjacent_piece
        )

        # Move the piece
        pipe.hmset(self.pc_puzzle_piece_key, {"x": self.target_x, "y": self.target_y})
        pipe.zadd(
            "pcx:{puzzle}".format(puzzle=self.puzzle), {self.piece: self.target_x}
        )
        pipe.zadd(
            "pcy:{puzzle}".format(puzzle=self.puzzle), {self.piece: self.target_y}
        )
        # Reset Piece Status for stacked (It's assumed that the piece being moved can't be an immovable piece)
        pipe.srem("pcstacked:{puzzle}".format(puzzle=self.puzzle), self.piece)
        pipe.hdel(
            "pc:{puzzle}:{piece}".format(puzzle=self.puzzle, piece=self.piece), "s"
        )
        lines.append(
            formatPieceMovementString(self.piece, x=self.target_x, y=self.target_y)
        )

        # Set immovable status if adjacent piece is immovable
        if adjacent_piece_props.get("s") == "1":
            pipe.hset(
                self.pc_puzzle_piece_key, "s", "1",
            )
            pipe.sadd("pcfixed:{puzzle}".format(puzzle=self.puzzle), self.piece)
            lines.append(formatPieceMovementString(self.piece, s="1"))
            for grouped_piece in self.all_other_pieces_in_piece_group:
                pc_puzzle_grouped_piece_key = "pc:{puzzle}:{grouped_piece}".format(
                    puzzle=self.puzzle, grouped_piece=grouped_piece
                )
                pipe.hset(pc_puzzle_grouped_piece_key, "s", "1")
                pipe.sadd("pcfixed:{puzzle}".format(puzzle=self.puzzle), grouped_piece)
                lines.append(formatPieceMovementString(grouped_piece, s="1"))

        new_piece_group = adjacent_piece_props.get("g", self.can_join_adjacent_piece)
        # Update Piece group to that of the adjacent piece since it may already be in a group
        pipe.sadd(
            "pcg:{puzzle}:{g}".format(puzzle=self.puzzle, g=new_piece_group),
            self.piece,
            self.can_join_adjacent_piece,
        )
        pipe.hset(
            self.pc_puzzle_piece_key, "g", new_piece_group,
        )
        pipe.hset(
            "pc:{puzzle}:{adjacent_piece}".format(
                puzzle=self.puzzle, adjacent_piece=self.can_join_adjacent_piece
            ),
            "g",
            new_piece_group,
        )
        lines.append(formatPieceMovementString(self.piece, g=new_piece_group))
        lines.append(
            formatPieceMovementString(self.can_join_adjacent_piece, g=new_piece_group)
        )
        if len(self.all_other_pieces_in_piece_group) != 0:
            lines.extend(
                self._update_grouped_pieces_positions(pipe, new_group=new_piece_group)
            )

        msg += "\n" + "\n".join(lines)
        return msg

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

    def _update_grouped_pieces_positions(
        self, pipe, new_group=None, status=None,
    ):
        "Update all other pieces x,y in group to the offset, if new_group then assign them to the new_group"

        lines = []
        for grouped_piece in self.grouped_piece_properties.keys():
            new_x = self.grouped_piece_properties[grouped_piece]["x"] + self.offset_x
            new_y = self.grouped_piece_properties[grouped_piece]["y"] + self.offset_y
            new_pc = {"x": new_x, "y": new_y}
            if new_group != None:
                # Remove from the old group and place in new_group
                new_pc["g"] = new_group
                pipe.sadd(
                    "pcg:{puzzle}:{g}".format(puzzle=self.puzzle, g=new_group),
                    grouped_piece,
                )
                pipe.srem(
                    "pcg:{puzzle}:{g}".format(
                        puzzle=self.puzzle, g=self.piece_properties.get("g")
                    ),
                    grouped_piece,
                )
            if status == "1":
                new_pc["s"] = "1"
                pipe.sadd("pcfixed:{puzzle}".format(puzzle=self.puzzle), grouped_piece)
                pipe.srem(
                    "pcstacked:{puzzle}".format(puzzle=self.puzzle), grouped_piece
                )
            pipe.hmset(
                "pc:{puzzle}:{grouped_piece}".format(
                    puzzle=self.puzzle, grouped_piece=grouped_piece
                ),
                new_pc,
            )
            pipe.zadd("pcx:{puzzle}".format(puzzle=self.puzzle), {grouped_piece: new_x})
            pipe.zadd("pcy:{puzzle}".format(puzzle=self.puzzle), {grouped_piece: new_y})
            lines.append(
                formatPieceMovementString(
                    grouped_piece, x=new_x, y=new_y, g=new_group, s=status
                )
            )
        if status == "1":
            pipe.sadd("pcfixed:{puzzle}".format(puzzle=self.puzzle), self.piece)
            pipe.srem("pcstacked:{puzzle}".format(puzzle=self.puzzle), self.piece)
            pipe.hset(
                "pc:{puzzle}:{piece}".format(puzzle=self.puzzle, piece=self.piece),
                "s",
                "1",
            )
        if new_group != None:
            # For the piece that doesn't need x,y updated remove from the old group and place in new_group
            pipe.sadd(
                "pcg:{puzzle}:{g}".format(puzzle=self.puzzle, g=new_group), self.piece
            )
            pipe.srem(
                "pcg:{puzzle}:{g}".format(
                    puzzle=self.puzzle, g=self.piece_properties.get("g")
                ),
                self.piece,
            )
            pipe.hset(
                "pc:{puzzle}:{piece}".format(puzzle=self.puzzle, piece=self.piece),
                "g",
                new_group,
            )
            lines.append(formatPieceMovementString(self.piece, g=new_group))
        return lines

    def _reset_pieces_in_proximity_stacked_status(self, pipe):
        msg = ""
        lines = []
        pipe.srem(
            "pcstacked:{puzzle}".format(puzzle=self.puzzle),
            *self.pieces_in_proximity_to_target
        )
        for piece_in_proximity in self.pieces_in_proximity_to_target:
            pipe.hdel(
                "pc:{puzzle}:{piece_in_proximity}".format(
                    puzzle=self.puzzle, piece_in_proximity=piece_in_proximity
                ),
                "s",
            )
            lines.append(formatPieceMovementString(piece_in_proximity, s=None))
        msg = "\n".join(lines)
        msg += "\n"
        return msg

    def _puzzle_completed(self):
        """Check if the puzzle is complete by counting pieces in immovable
        adjacent piece group and piece group."""
        return (
            self.adjacent_piece_properties[self.can_join_adjacent_piece].get("s") == "1"
            and (
                self.adjacent_piece_group_counts.get(
                    self.adjacent_piece_properties[self.can_join_adjacent_piece].get(
                        "g"
                    )
                )
                + len(self.all_other_pieces_in_piece_group)
                + 1
            )
            == self.piece_count
        )
