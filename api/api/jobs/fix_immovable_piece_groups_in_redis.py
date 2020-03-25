"""fix_immovable_piece_groups.py
Fix any separate immovable piece groups in redis.

Usage: fix_immovable_piece_groups.py <site.cfg> [--cleanup]
       fix_immovable_piece_groups.py --help

Options:
  -h --help         Show this screen.
  --cleanup         ...
"""

from docopt import docopt

from api.database import rowify, read_query_file
from api.tools import loadConfig, get_db, get_redis_connection, deletePieceDataFromRedis
from api.constants import MAINTENANCE


def find_puzzles_in_redis(results={}):
    """
    For each puzzle that is active in redis (is in pcupdates); check the
    immovable piece group counts.  Fail any that do not equal the count for the
    top left piece group.
    """
    _results = results.copy()
    cur = db.cursor()

    puzzles_in_redis = redis_connection.zrange("pcupdates", 0, -1)
    for puzzle in puzzles_in_redis:
        test_result = _results.get(puzzle, {"puzzle": puzzle, "msg": "", "test": []})
        test_result["test"].append("redis")
        _results.update({puzzle: test_result})
        (result, col_names) = rowify(
            cur.execute(
                read_query_file("select_puzzle_top_left_piece_for_puzzle.sql"),
                {"id": puzzle},
            ).fetchall(),
            cur.description,
        )
        if not result or not result[0]:
            # Test failed.
            test_result[
                "msg"
            ] = "{msg} Failed to find top left piece for puzzle {puzzle}".format(
                msg=test_result.get("msg", ""), puzzle=puzzle
            )
            test_result["status"] = "fail"
            continue

        top_left_piece = result[0]
        test_result["puzzle_id"] = top_left_piece["puzzle_id"]

        # Compare the counts for the pcfixed and the top left piece group.  They
        # should be the same.
        pcfixed_count = redis_connection.scard("pcfixed:{puzzle}".format(puzzle=puzzle))
        pcg_for_top_left = redis_connection.hget(
            "pc:{puzzle}:{id}".format(puzzle=puzzle, id=top_left_piece["id"]), "g"
        )
        immovable_top_left_group_count = redis_connection.scard(
            "pcg:{puzzle}:{group}".format(puzzle=puzzle, group=pcg_for_top_left)
        )
        if pcfixed_count == immovable_top_left_group_count:
            # Test passed.
            test_result[
                "msg"
            ] = "{msg} {puzzle_id} {puzzle} all immovable pieces are in the same group as top left".format(
                msg=test_result.get("msg", ""),
                puzzle_id=top_left_piece["puzzle_id"],
                puzzle=puzzle,
            )
            test_result["status"] = "pass"
            continue
        else:
            # Test failed.
            test_result[
                "msg"
            ] = "{msg} {puzzle_id} {puzzle} not all immovable pieces are in the same group as top left".format(
                msg=test_result.get("msg", ""),
                puzzle_id=top_left_piece["puzzle_id"],
                puzzle=puzzle,
            )
            test_result["status"] = "fail"
    return _results


def find_puzzles_in_database(results={}):
    """
    """
    _results = results.copy()
    cur = db.cursor()

    (puzzles_in_database, col_names) = rowify(
        cur.execute(
            read_query_file("select_all_puzzles_with_rendered_pieces.sql"),
        ).fetchall(),
        cur.description,
    )
    if not puzzles_in_database:
        # no matching puzzles found
        return _results

    for puzzle_data in puzzles_in_database:
        puzzle = puzzle_data["id"]
        test_result = _results.get(
            puzzle,
            {
                "puzzle": puzzle,
                "puzzle_id": puzzle_data["puzzle_id"],
                "msg": "",
                "test": [],
            },
        )
        test_result["test"].append("database")
        _results.update({puzzle: test_result})

        # TODO: Check piece data for this puzzle to see if pieces that are
        # immovable have the same parent as top left piece.
        (immovable_pieces, col_names) = rowify(
            cur.execute(
                read_query_file("select_immovable_piece_groups_for_puzzle.sql"),
                {"puzzle": puzzle},
            ).fetchall(),
            cur.description,
        )

        # Fail if no immovable piece groups
        if not immovable_pieces:
            test_result[
                "msg"
            ] = "{msg} {puzzle_id} {puzzle} no immovable piece groups found in database".format(
                msg=test_result.get("msg", ""),
                puzzle_id=puzzle_data["puzzle_id"],
                puzzle=puzzle,
            )
            test_result["status"] = "fail"

        # Fail if more than one immovable piece group
        if len(immovable_pieces) > 1:
            test_result[
                "msg"
            ] = "{msg} {puzzle_id} {puzzle} multiple immovable piece groups found in database".format(
                msg=test_result.get("msg", ""),
                puzzle_id=puzzle_data["puzzle_id"],
                puzzle=puzzle,
            )
            test_result["status"] = "fail"

        # Pass if only one immovable piece group found
        if len(immovable_pieces) == 1:
            test_result[
                "msg"
            ] = "{msg} {puzzle_id} {puzzle} single immovable piece group found in database".format(
                msg=test_result.get("msg", ""),
                puzzle_id=puzzle_data["puzzle_id"],
                puzzle=puzzle,
            )
            test_result["status"] = "pass"

    return _results


def fix_redis_piece_groups():
    ""
    # TODO: implement a fix for when there are multiple immovable piece groups
    # that have a different piece group then the top left piece.


def fix_db_piece_parents():
    ""
    # TODO: implement a fix for data stored in Piece table when multiple pieces
    # have status of immovable, but do not have the same parent as top left
    # piece.


if __name__ == "__main__":
    args = docopt(__doc__)
    config_file = args["<site.cfg>"]
    config = loadConfig(config_file)

    db = get_db(config)
    redis_connection = get_redis_connection(config)

    # Check puzzles in redis data store
    multiple_immovable_piece_group_results = find_puzzles_in_redis(results={})

    # TODO: Check puzzles in SQL database
    multiple_immovable_piece_group_results = find_puzzles_in_database(
        results=multiple_immovable_piece_group_results
    )

    # TODO: Fix puzzles that failed the test
    fix_redis_piece_groups()
    fix_db_piece_parents()

    # Print out the results
    failed_results = list(
        filter(
            lambda x: x["status"] == "fail",
            multiple_immovable_piece_group_results.values(),
        )
    )
    passed_results = list(
        filter(
            lambda x: x["status"] == "pass",
            multiple_immovable_piece_group_results.values(),
        )
    )
    redis_tests = list(
        filter(
            lambda x: "redis" in x["test"],
            multiple_immovable_piece_group_results.values(),
        )
    )
    database_tests = list(
        filter(
            lambda x: "database" in x["test"],
            multiple_immovable_piece_group_results.values(),
        )
    )
    for result in failed_results:
        print(result["msg"])
    print(
        """
Total results:
Redis puzzles tested: {redis_count}
Database puzzles tested: {database_count}
Pass: {pass_count}
Fail: {fail_count}
Fixed: 0
""".format(
            pass_count=len(passed_results),
            fail_count=len(failed_results),
            redis_count=len(redis_tests),
            database_count=len(database_tests),
        )
    )
    for result in failed_results:
        print(
            "{puzzle} {puzzle_id}".format(
                puzzle=result["puzzle"], puzzle_id=result.get("puzzle_id")
            )
        )

else:
    # Support for using within the Flask app.
    config = loadConfig("site.cfg")

    db = get_db(config)
    redis_connection = get_redis_connection(config)
