import math

from flask import current_app, request, abort, json, make_response
from flask.views import MethodView

from api.app import db
from api.user import user_id_from_ip, user_not_banned
from api.database import fetch_query_string, rowify
from api.constants import (
    ACTIVE,
    IN_QUEUE,
    COMPLETED,
    FROZEN,
    IN_RENDER_QUEUE,
    REBUILD,
    RENDERING,
    RENDERING_FAILED,
)

STATUS_RECENT = "recent"
STATUS_ACTIVE = "active"
STATUS_IN_QUEUE = "in_queue"
STATUS_COMPLETE = "complete"
STATUS_FROZEN = "frozen"
STATUS_UNAVAILABLE = "unavailable"

STATUS = {
    STATUS_RECENT,
    STATUS_ACTIVE,
    STATUS_IN_QUEUE,
    STATUS_COMPLETE,
    STATUS_FROZEN,
    STATUS_UNAVAILABLE,
}

TYPE_ORIGINAL = "original"
TYPE_INSTANCE = "instance"
TYPE = {TYPE_ORIGINAL, TYPE_INSTANCE}

ORDERBY_M_DATE = "m_date"
ORDERBY_PIECES = "pieces"
ORDERBY_QUEUE = "queue"
ORDERBY = {ORDERBY_M_DATE, ORDERBY_PIECES, ORDERBY_QUEUE}

page_size = 44


def hidden_preview(puzzle_data):
    if puzzle_data.get("has_hidden_preview"):
        puzzle_data["src"] = ""
        puzzle_data["title"] = ""
        puzzle_data["author_link"] = ""
        puzzle_data["author_name"] = ""
        puzzle_data["source"] = ""
        puzzle_data["license_source"] = ""
        puzzle_data["license_name"] = ""
        puzzle_data["license_title"] = ""
    return puzzle_data


class InternalPuzzleRenderedResourcesListView(MethodView):
    """"""

    def get(self):

        url_match = request.args.get("url_match", "/resources/%")

        cur = db.cursor()

        result = cur.execute(
            fetch_query_string("select_rendered_puzzle_files_with_url_like.sql"),
            {"url_match": url_match},
        ).fetchall()
        if not result:
            puzzle_files = []
        else:
            (result, col_names) = rowify(result, cur.description)
            puzzle_files = result

        response = {
            "puzzle_files": puzzle_files,
        }

        cur.close()

        return make_response(json.jsonify(response), 200)



class PlayerPuzzleListView(MethodView):
    """"""

    decorators = [user_not_banned]

    def get(self):
        """
        /newapi/player-puzzle-list/

        returns
        {
        puzzles: [],
        }

        """

        ip = request.headers.get("X-Real-IP")
        user = int(current_app.secure_cookie.get("user") or user_id_from_ip(ip))

        cur = db.cursor()

        puzzle_list = []
        result = cur.execute(
            fetch_query_string("select_available_player_puzzle_images.sql"),
            {"player": user, "count": 40},
        ).fetchall()
        if result:
            (result, col_names) = rowify(result, cur.description)
            puzzle_list = list(
                filter(lambda puzzle: puzzle["puzzle_id"], result)
            ) + list(filter(lambda puzzle: not puzzle["puzzle_id"], result))

        puzzle_list = list(map(hidden_preview, puzzle_list))
        response = {
            "puzzles": puzzle_list,
        }

        cur.close()

        return make_response(json.jsonify(response), 200)


class GalleryPuzzleListView(MethodView):
    """"""

    def get(self):
        """
        /newapi/gallery-puzzle-list/

        returns
        {
        puzzles: [],
        }

        """

        # The response is cacheable so need to check for user
        # ip = request.headers.get('X-Real-IP')
        # user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(ip))

        cur = db.cursor()
        puzzle_list = []

        for low, high in current_app.config["SKILL_LEVEL_RANGES"]:
            result = cur.execute(
                fetch_query_string("select_available_puzzle_images--gallery.sql"),
                {"pieces_min": low, "pieces_max": high},
            ).fetchall()
            if result:
                (result, col_names) = rowify(result, cur.description)
                result = list(map(hidden_preview, result))
                puzzle_list = puzzle_list + result

        puzzle_list.sort(key=lambda x: x.get("seconds_from_now") or 1)

        response = {
            "puzzles": puzzle_list,
        }

        cur.close()

        return make_response(json.jsonify(response), 200)
