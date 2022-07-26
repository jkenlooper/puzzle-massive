"""fix_immovable_piece_groups.py
Fix any separate immovable piece groups in redis.

Usage: fix_immovable_piece_groups.py [--config <file>] [--cleanup]
       fix_immovable_piece_groups.py --help

Options:
  -h --help         Show this screen.
  --config <file>   Set config file. [default: site.cfg]
  --cleanup         ...
"""

import os

from docopt import docopt

from api.app import redis_connection, db, make_app
from api.database import rowify, read_query_file
from api.tools import loadConfig


def find_puzzles_in_redis(results={}):
    """
    For each puzzle that is active in redis (is in pcupdates); check the
    immovable piece group counts.  Fail any that do not equal the count for the
    top left piece group.
    """
    _results = results.copy()

    puzzles_in_redis = redis_connection.zrange("pcupdates", 0, -1)
    for puzzle in puzzles_in_redis:
        cur = db.cursor()
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
        cur.close()
        if not result or not result[0]:
            # Test failed.
            test_result[
                "msg"
            ] = "{msg} Failed to find top left piece for puzzle {puzzle}".format(
                msg=test_result.get("msg", ""), puzzle=puzzle
            )
            test_result["status"] = "fail"
            test_result["reason"] = "fail_no_top_left_piece"
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
            test_result["reason"] = "pass"
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
            test_result["reason"] = "fail_pcfixed_outside_of_top_left"
    return _results


def find_puzzles_in_database(results={}):
    """ """
    _results = results.copy()
    cur = db.cursor()

    (puzzles_in_database, col_names) = rowify(
        cur.execute(
            read_query_file("select_all_puzzles_with_rendered_pieces.sql"),
        ).fetchall(),
        cur.description,
    )
    cur.close()
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

        cur = db.cursor()
        (immovable_pieces, col_names) = rowify(
            cur.execute(
                read_query_file("select_immovable_piece_groups_for_puzzle.sql"),
                {"puzzle": puzzle},
            ).fetchall(),
            cur.description,
        )
        cur.close()

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
            test_result["reason"] = "fail_no_immovable_piece_groups"

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
            test_result["reason"] = "fail_multiple_immovable_piece_groups"

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
            test_result["reason"] = "pass"

    return _results


def fix_redis_piece_groups(puzzles, results={}):
    """Fix for when there are multiple immovable piece groups that have
    a different piece group then the top left piece."""
    _results = results.copy()

    # Find each group that is not the same as the top left piece and remove
    # those pieces from the pcfixed redis smembers
    print(f"failed redis puzzles: {puzzles}")
    for puzzle in puzzles:
        cur = db.cursor()
        (result, col_names) = rowify(
            cur.execute(
                read_query_file("select_puzzle_top_left_piece_for_puzzle.sql"),
                {"id": puzzle},
            ).fetchall(),
            cur.description,
        )
        cur.close()
        if not result or not result[0]:
            continue

        top_left_piece = result[0]
        pcg_for_top_left = redis_connection.hget(
            "pc:{puzzle}:{id}".format(puzzle=puzzle, id=top_left_piece["id"]), "g"
        )

        # Fix by resetting the pcfixed members back to only those for the top
        # left piece group.
        redis_connection.sinterstore(
            f"pcfixed:{puzzle}",
            f"pcfixed:{puzzle}",
            "pcg:{puzzle}:{group}".format(puzzle=puzzle, group=pcg_for_top_left),
        )

        _results[puzzle]["fixed"] = True
    return _results


def fix_db_piece_parents(puzzles, results={}):
    """
    Fix for data stored in Piece table when multiple pieces have status of
    immovable, but do not have the same parent as top left piece.
    """
    _results = results.copy()

    print(f"Failed db puzzles: {puzzles}")
    for puzzle in puzzles:
        cur = db.cursor()
        (result, col_names) = rowify(
            cur.execute(
                read_query_file("select_top_left_immovable_piece_for_puzzle.sql"),
                {"id": puzzle},
            ).fetchall(),
            cur.description,
        )
        cur.close()
        if not result or not result[0]:
            continue
        if len(result) > 1:
            continue

        top_left_piece = result[0]
        pcg_for_top_left = top_left_piece["parent"]

        cur = db.cursor()
        cur.execute(
            read_query_file("reset_piece_immovable_status_for_not_parent.sql"),
            {"puzzle": puzzle, "parent": pcg_for_top_left},
        )
        cur.close()
        db.commit()

        _results[puzzle]["fixed"] = True
    return _results


def do_it():
    # Check puzzles in redis data store
    multiple_immovable_piece_group_results = find_puzzles_in_redis(results={})

    # Check puzzles in SQL database
    multiple_immovable_piece_group_results = find_puzzles_in_database(
        results=multiple_immovable_piece_group_results
    )

    failed_puzzles_in_redis_with_pcfixed_outside_of_top_left = list(
        map(
            lambda x: int(x["puzzle"]),
            filter(
                lambda x: x["status"] == "fail"
                and "redis" in x["test"]
                and x["reason"] == "fail_pcfixed_outside_of_top_left",
                multiple_immovable_piece_group_results.values(),
            ),
        )
    )

    multiple_immovable_piece_group_results = fix_redis_piece_groups(
        failed_puzzles_in_redis_with_pcfixed_outside_of_top_left,
        results=multiple_immovable_piece_group_results,
    )

    failed_puzzles_in_database_with_multiple_immovable_piece_groups = list(
        map(
            lambda x: int(x["puzzle"]),
            filter(
                lambda x: x["status"] == "fail"
                and "database" in x["test"]
                and x["reason"] == "fail_multiple_immovable_piece_groups",
                multiple_immovable_piece_group_results.values(),
            ),
        )
    )
    fix_db_piece_parents(
        failed_puzzles_in_database_with_multiple_immovable_piece_groups,
        results=multiple_immovable_piece_group_results,
    )

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
    fixed_results = list(
        filter(
            lambda x: x.get("fixed"),
            multiple_immovable_piece_group_results.values(),
        )
    )
    for result in failed_results:
        print(result["msg"])
    for result in failed_results:
        print(
            "{puzzle} {puzzle_id}".format(
                puzzle=result["puzzle"], puzzle_id=result.get("puzzle_id")
            )
        )
    print("fixed:")
    for result in fixed_results:
        print(
            "{puzzle} {puzzle_id}".format(
                puzzle=result["puzzle"], puzzle_id=result.get("puzzle_id")
            )
        )
    print(
        """
Total results:
Redis puzzles tested: {redis_count}
Database puzzles tested: {database_count}
Pass: {pass_count}
Fail: {fail_count}
Fixed: {fixed_count}
""".format(
            pass_count=len(passed_results),
            fail_count=len(failed_results),
            redis_count=len(redis_tests),
            database_count=len(database_tests),
            fixed_count=len(fixed_results),
        )
    )


if __name__ == "__main__":
    args = docopt(__doc__)
    config_file = args["--config"]
    config = loadConfig(config_file)
    cookie_secret = config.get("SECURE_COOKIE_SECRET")

    confirm = input(
        "Before running this script it is recommended to stop the application to avoid potential issues with multiple processes writing to the database.\nWARNING: This script does not automatically stop the application.\n  Continue? [y/n]"
    )
    if confirm != "y":
        print("Cancelled action")
        os.sys.exit(0)

    # Database is writable so the query to find and fix the issues with the
    # pieces are a single transaction. Otherwise would need to create a single
    # purpose api endpoint to accomplish this.
    app = make_app(
        config=config_file, cookie_secret=cookie_secret, database_writable=True
    )

    with app.app_context():
        do_it()
