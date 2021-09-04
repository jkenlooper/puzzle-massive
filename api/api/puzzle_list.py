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


def build_select_available_puzzle_sql(query_file, status, type):
    """
    The sqlite bind params don't support expanding lists, so doing this
    manually.  Careful here to avoid sql injection attacks.
    """
    recent_status = set()  # include false values for is_recent
    active_status = {
        0,
    }  # include false values for is_active
    status_ids = set()
    for name in status:
        if name == STATUS_RECENT:
            recent_status.add(1)
            status_ids.add(ACTIVE)

        elif name == STATUS_ACTIVE:
            recent_status.add(0)
            recent_status.add(1)
            active_status.add(1)
            status_ids.add(ACTIVE)

        elif name == STATUS_IN_QUEUE:
            recent_status.add(0)
            status_ids.add(IN_QUEUE)

        elif name == STATUS_COMPLETE:
            recent_status.add(0)
            status_ids.add(COMPLETED)

        elif name == STATUS_FROZEN:
            recent_status.add(0)
            status_ids.add(FROZEN)

        elif name == STATUS_UNAVAILABLE:
            recent_status.add(0)
            status_ids.add(REBUILD)
            status_ids.add(IN_RENDER_QUEUE)
            status_ids.add(RENDERING)
            status_ids.add(RENDERING_FAILED)

    original_type = set()
    for name in type:
        if name == TYPE_ORIGINAL:
            original_type.add(1)
        elif name == TYPE_INSTANCE:
            original_type.add(0)

    query = fetch_query_string(query_file)

    query = query.format(
        status="({})".format(", ".join(map(str, status_ids))),
        recent_status="({})".format(", ".join(map(str, recent_status))),
        active_status="({})".format(", ".join(map(str, active_status))),
        original_type="({})".format(", ".join(map(str, original_type))),
    )
    # current_app.logger.debug(query)

    return query


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


class PuzzleListView(MethodView):
    """"""

    def get(self):
        """
        /newapi/puzzle-list/?status=...&status=...&
        status: recent, active, new, queue, complete, frozen, unavailable
        pieces_min: number
        pieces_max: number
        type: original, instance
        orderby: m_date, pieces, queue
        page: number

        returns
        {
        puzzles: [],
        totalPuzzleCount: 899,
        puzzleCount: 555,
        pageSize: 44,
        currentPage: 1,
        maxPieces: 6232,
        }

        """
        try:
            page = int(request.args.get("page", "1"))
            pieces_min = int(request.args.get("pieces_min", "0"))
            pieces_max = int(request.args.get("pieces_max", "60000"))
        except ValueError as err:
            abort(400)

        status = set(request.args.getlist("status"))
        status = status.intersection(STATUS)
        status = tuple(status)
        # current_app.logger.debug('status {}'.format(status))

        type = set(request.args.getlist("type"))
        if len(type) > 0 and not type.issubset(TYPE):
            abort(400)
        type = tuple(type)

        orderby = request.args.get("orderby", ORDERBY_M_DATE)
        if orderby not in ORDERBY:
            abort(400)

        # TODO: this request is cacheable so need to check for user
        # ip = request.headers.get('X-Real-IP')
        # user = int(current_app.secure_cookie.get(u'user') or user_id_from_ip(ip))

        cur = db.cursor()

        total_puzzle_count = 0
        max_pieces = 0
        result = cur.execute(
            fetch_query_string("select_total_available_puzzle_images.sql")
        ).fetchall()
        if result:
            (result, col_names) = rowify(result, cur.description)
            result = result[0]
            total_puzzle_count = result["total_puzzle_count"]
            max_pieces = result["max_pieces"]

        puzzle_count = 0
        select_available_puzzle_image_count = build_select_available_puzzle_sql(
            "select_available_puzzle_image_count.sql", status, type
        )
        # current_app.logger.debug(select_available_puzzle_image_count)

        result = cur.execute(
            select_available_puzzle_image_count,
            {
                "pieces_min": pieces_min,
                "pieces_max": pieces_max,
            },
        ).fetchall()
        if result:
            puzzle_count = result[0][0]

        page_max = math.ceil(puzzle_count / page_size)
        page = min(page_max, page)

        select_available_puzzle_images = ""
        if orderby == ORDERBY_PIECES:
            select_available_puzzle_images = build_select_available_puzzle_sql(
                "select_available_puzzle_images--orderby-pieces.sql", status, type
            )
        elif orderby == ORDERBY_QUEUE:
            select_available_puzzle_images = build_select_available_puzzle_sql(
                "select_available_puzzle_images--orderby-queue.sql", status, type
            )
        else:  # ORDERBY_M_DATE
            select_available_puzzle_images = build_select_available_puzzle_sql(
                "select_available_puzzle_images--orderby-m_date.sql", status, type
            )

        result = cur.execute(
            select_available_puzzle_images,
            {
                "pieces_min": pieces_min,
                "pieces_max": pieces_max,
                "page_size": page_size,
                "offset": (page - 1) * page_size,
            },
        ).fetchall()
        if not result:
            puzzle_list = []
        else:
            (result, col_names) = rowify(result, cur.description)
            puzzle_list = result

        puzzle_list = list(map(hidden_preview, puzzle_list))

        response = {
            "puzzles": puzzle_list,
            "totalPuzzleCount": total_puzzle_count,
            "puzzleCount": puzzle_count,
            "pageSize": page_size,
            "currentPage": page,
            "maxPieces": max_pieces,
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
        user = int(current_app.secure_cookie.get(u"user") or user_id_from_ip(ip))

        cur = db.cursor()

        puzzle_list = []
        result = cur.execute(
            fetch_query_string("select_available_player_puzzle_images.sql"),
            {"player": user},
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
                {"pieces_min": low, "pieces_max": high, "count": 2},
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
