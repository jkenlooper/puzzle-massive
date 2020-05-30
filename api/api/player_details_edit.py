"Admin Player Edit"

from flask import current_app, redirect, request, make_response, abort
from flask.views import MethodView

from api.app import db
from api.database import rowify, fetch_query_string, delete_puzzle_resources
from api.constants import USER_NAME_MAXLENGTH, EMAIL_MAXLENGTH
from api.tools import normalize_name_from_display_name, purge_route_from_nginx_cache

SLOT_ACTIONS = ("add", "delete")


class AdminPlayerDetailsEditView(MethodView):
    """
    Handle editing player details.
    """

    def post(self):
        "Route is protected by basic auth in nginx"
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        player = args.get("player")
        if not player:
            abort(400)
        email_verified = int(args.get("email_verified", "0"))
        if not email_verified in (0, 1):
            abort(400)
        name_approved = int(args.get("name_approved", "0"))
        if not name_approved in (0, 1):
            abort(400)

        # name is always converted to lowercase and display_name preserves
        # original case.
        display_name = args.get("name", "").strip()
        name = normalize_name_from_display_name(display_name)
        if len(display_name) > USER_NAME_MAXLENGTH:
            abort(400)

        email = args.get("email", "").strip().lower()
        if len(email) > EMAIL_MAXLENGTH:
            abort(400)

        cur = db.cursor()

        result = cur.execute(
            fetch_query_string("user-has-player-account.sql"), {"player_id": player}
        ).fetchone()
        if not result or result[0] == 0:
            cur.execute(
                fetch_query_string("init-player-account-for-user.sql"),
                {"player_id": player},
            )
            db.commit()

        result = cur.execute(
            fetch_query_string("select-admin-player-details-for-player-id.sql"),
            {"player_id": player},
        ).fetchall()
        if not result:
            cur.close()
            db.commit()
            abort(400)
        (result, col_names) = rowify(result, cur.description)
        existing_player_data = result[0]

        if email == "":
            cur.execute(
                fetch_query_string("remove-player-account-email.sql"),
                {"player_id": player},
            )
        else:
            cur.execute(
                fetch_query_string("update-player-account-email.sql"),
                {"player_id": player, "email": email},
            )

        cur.execute(
            fetch_query_string("update-player-account-email-verified.sql"),
            {"player_id": player, "email_verified": email_verified,},
        )

        cur.execute(
            fetch_query_string("update-user-points.sql"),
            {
                "player_id": player,
                "points": int(args.get("dots", existing_player_data["dots"])),
                "POINTS_CAP": current_app.config["POINTS_CAP"],
            },
        )

        if name == "":
            cur.execute(
                fetch_query_string("remove-user-name-on-name-register-for-player.sql"),
                {"player_id": player,},
            )
        else:
            if existing_player_data["name"] != name:
                result = cur.execute(
                    fetch_query_string("select-unclaimed-name-on-name-register.sql"),
                    {"name": name,},
                ).fetchall()
                if result:
                    (result, col_names) = rowify(result, cur.description)
                    unclaimed_name_data = result[0]
                    if unclaimed_name_data["approved_date"] == None:
                        # name has been rejected
                        if name_approved == 1:
                            # override the rejected name and let player claim it
                            cur.execute(
                                fetch_query_string(
                                    "remove-user-name-on-name-register-for-player.sql"
                                ),
                                {"player_id": player,},
                            )
                            cur.execute(
                                fetch_query_string(
                                    "claim-rejected-user-name-on-name-register-for-player.sql"
                                ),
                                {"player_id": player, "name": name,},
                            )
                    else:
                        # name can be claimed
                        cur.execute(
                            fetch_query_string(
                                "remove-user-name-on-name-register-for-player.sql"
                            ),
                            {"player_id": player,},
                        )
                        cur.execute(
                            fetch_query_string(
                                "claim-user-name-on-name-register-for-player.sql"
                            ),
                            {
                                "player_id": player,
                                "display_name": display_name,
                                "name": name,
                                "time": "+1 second",
                            },
                        )
                else:
                    # The name is new and not in the NameRegister.  Add it and
                    # mark it for auto-approval.
                    cur.execute(
                        fetch_query_string(
                            "remove-user-name-on-name-register-for-player.sql"
                        ),
                        {"player_id": player,},
                    )
                    cur.execute(
                        fetch_query_string(
                            "add-user-name-on-name-register-for-player.sql"
                        ),
                        {
                            "player_id": player,
                            "name": name,
                            "display_name": display_name,
                            "time": "+1 second",
                        },
                    )

        if existing_player_data["name_approved"] == 1 and name_approved == 0:
            # Place this name on reject list
            cur.execute(
                fetch_query_string("reject-name-on-name-register.sql"), {"name": name,}
            )

        if existing_player_data["name_approved"] == 0 and name_approved == 1:
            cur.execute(
                fetch_query_string("update-user-name-approved.sql"),
                {"player_id": player, "name_approved": name_approved,},
            )

        cur.close()
        db.commit()

        purge_route_from_nginx_cache(
            "/chill/site/internal/player-bit/{}/".format(player),
            current_app.config.get("PURGEURLLIST"),
        )

        return redirect(
            "/chill/site/admin/player/details/{player}/".format(player=player)
        )


class AdminPlayerDetailsSlotsView(MethodView):
    """
    Handle editing player puzzle instance slots.
    """

    def post(self):
        args = {}
        if request.form:
            args.update(request.form.to_dict(flat=True))

        # Verify args
        action = args.get("action")
        if action not in SLOT_ACTIONS:
            abort(400)

        player = args.get("player")
        if not player:
            abort(400)

        cur = db.cursor()

        if action == "add":
            cur.execute(
                fetch_query_string("add-new-user-puzzle-slot.sql"), {"player": player}
            )
        elif action == "delete":
            cur.execute(
                fetch_query_string("delete-user-puzzle-slot.sql"), {"player": player}
            )

        cur.close()
        db.commit()

        return redirect(
            "/chill/site/admin/player/details/{player}/".format(player=player)
        )
