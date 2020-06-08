from flask import current_app, make_response, request, abort, json
from flask.views import MethodView

from api.app import db, redis_connection
from api.database import fetch_query_string, rowify

puzzle_file_names_with_no_attribution = {"pzz", "pieces"}
puzzle_file_names_with_optional_attribution = {"original", "preview_full"}
puzzle_file_names = puzzle_file_names_with_no_attribution.union(
    puzzle_file_names_with_optional_attribution
)


def add_puzzle_file(puzzle_id, file_name, url):
    "Only supports pzz and pieces files for now"

    cur = db.cursor()
    result = cur.execute(
        fetch_query_string("select-internal-puzzle-details-for-puzzle_id.sql"),
        {"puzzle_id": puzzle_id},
    ).fetchall()
    if not result:
        err_msg = {"msg": "No puzzle found", "status_code": 400}
        cur.close()
        return err_msg

    (result, col_names) = rowify(result, cur.description)
    puzzle_data = result[0]
    puzzle = puzzle_data["id"]

    result = cur.execute(
        fetch_query_string("add-puzzle-file.sql"),
        {"puzzle": puzzle, "name": file_name, "url": url},
    )
    db.commit()

    cur.close()

    msg = {"rowcount": result.rowcount, "msg": "Inserted", "status_code": 200}
    return msg


def delete_puzzle_file(puzzle_id, file_name):
    "Only supports pzz and pieces files for now"

    cur = db.cursor()
    result = cur.execute(
        fetch_query_string("select-internal-puzzle-details-for-puzzle_id.sql"),
        {"puzzle_id": puzzle_id},
    ).fetchall()
    if not result:
        err_msg = {"msg": "No puzzle found", "status_code": 400}
        cur.close()
        return err_msg

    (result, col_names) = rowify(result, cur.description)
    puzzle_data = result[0]
    puzzle = puzzle_data["id"]

    result = cur.execute(
        fetch_query_string("delete_puzzle_file_with_name_for_puzzle.sql"),
        {"puzzle": puzzle, "name": file_name},
    )
    db.commit()
    cur.close()

    msg = {"rowcount": result.rowcount, "msg": "Deleted", "status_code": 200}
    return msg


class InternalPuzzleFileView(MethodView):
    """
    Handle internal requests for puzzle files with names 'pzz' and 'pieces'.
    Doesn't support other puzzle files that use attribution at this time.
    """

    def post(self, puzzle_id, file_name):
        "Add a puzzle file url to the database."

        if file_name not in puzzle_file_names_with_no_attribution:
            err_msg = {
                "msg": "File with that name is not supported",
                "status_code": 400,
            }
            return make_response(json.jsonify(err_msg), err_msg["status_code"])

        data = request.get_json(silent=True)
        if not data:
            err_msg = {"msg": "No JSON data sent", "status_code": 400}
            return make_response(json.jsonify(err_msg), err_msg["status_code"])
        if not {"url",}.issuperset(data.keys()):
            err_msg = {"msg": "Extra fields in JSON data were sent", "status_code": 400}
            return make_response(json.jsonify(err_msg), err_msg["status_code"])

        response_msg = add_puzzle_file(puzzle_id, file_name, data["url"])
        return make_response(json.jsonify(response_msg), response_msg["status_code"])

    def delete(self, puzzle_id, file_name):
        "Delete a puzzle file from the database."
        # api/api/jobs/pieceRenderer.py render
        # internal-puzzle-pieces "delete from Piece where puzzle = :puzzle"
        data = request.get_json(silent=True)
        if data:
            err_msg = {
                "msg": "No JSON payload should be sent with DELETE",
                "status_code": 400,
            }
            return make_response(json.jsonify(err_msg), err_msg["status_code"])

        if file_name not in puzzle_file_names_with_no_attribution:
            err_msg = {
                "msg": "File with that name is not supported",
                "status_code": 400,
            }
            return make_response(json.jsonify(err_msg), err_msg["status_code"])

        response_msg = delete_puzzle_file(puzzle_id, file_name)
        return make_response(json.jsonify(response_msg), response_msg["status_code"])
