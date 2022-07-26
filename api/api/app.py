import os

from werkzeug.local import LocalProxy
from flask import Flask, g, current_app
import sqlite3

from rq import Queue

from api.flask_secure_cookie import SecureCookie
from api.tools import get_db, get_redis_connection, files_loader


class API(Flask):
    "API App"


def set_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = get_db(current_app.config)
    return db


db = LocalProxy(set_db)


def set_redis_connection():
    get_redis_connection(current_app.config)
    redis_connection = getattr(g, "_redis_connection", None)
    if redis_connection is None:
        redis_connection = g._redis_connection = get_redis_connection(
            current_app.config
        )
    return redis_connection


redis_connection = LocalProxy(set_redis_connection)


def make_app(config=None, database_writable=False, **kw):
    app = API("api")
    app.config_file = config

    if config:
        config_file = (
            config if config[0] == os.sep else os.path.join(os.getcwd(), config)
        )
        app.config.from_pyfile(config_file)

    app.config.update(kw, database_writable=database_writable)

    # Cookie secret value will be read from app.config.
    # If it does not exist, an exception will be thrown.
    #
    # You can also set the cookie secret in the SecureCookie initializer:
    # secure_cookie = SecureCookie(app, cookie_secret="MySecret")
    #
    app.secure_cookie = SecureCookie(app, cookie_secret=kw["cookie_secret"])

    app.queries = files_loader("queries")

    app.cleanupqueue = Queue("puzzle_cleanup", connection=redis_connection)
    app.createqueue = Queue("puzzle_create", connection=redis_connection)
    app.unsplashqueue = Queue("unsplash_image_fetch", connection=redis_connection)

    @app.teardown_appcontext
    def teardown_db(exception):
        db = getattr(g, "_database", None)
        if db is not None:
            db.close()

    archive_directory = app.config.get("PUZZLE_ARCHIVE")
    try:
        os.mkdir(archive_directory)
    except OSError:
        # directory already exists
        pass

    resources_directory = app.config.get("PUZZLE_RESOURCES")
    try:
        os.mkdir(resources_directory)
    except OSError:
        # directory already exists
        pass

    # import the views and sockets
    from api.piece import PuzzlePieceView
    from api.pieces import (
        PuzzlePiecesView,
        PuzzlePieceUpdatesView,
        InternalPuzzlePiecesView,
        InternalPuzzlePublishMove,
    )
    from api.puzzle_file import InternalPuzzleFileView
    from api.timeline import InternalPuzzleTimelineView

    # from api.reset import PuzzlePiecesResetView
    from api.rebuild import PuzzlePiecesRebuildView
    from api.instance import CreatePuzzleInstanceView
    from api.upload import (
        PuzzleUploadView,
        AdminPuzzlePromoteSuggestedView,
        AdminPuzzleUnsplashBatchView,
    )
    from api.suggest_image import SuggestImageView
    from api.render import RenderPuzzlesView
    from api.user import (
        CurrentUserIDView,
        UserDetailsView,
        GenerateAnonymousLogin,
        GenerateAnonymousLoginByToken,
        UserLogoutView,
        UserLoginView,
        AdminUserLoginView,
        ClaimUserByTokenView,
        InternalUserDetailsView,
        AdminBannedUserList,
        BanishSelf,
    )
    from api.bit import ChooseBitView, ClaimBitView, ClaimUserView
    from api.stats import (
        PuzzleStatsView,
        PlayerRanksView,
        PuzzleActiveCountView,
        PlayerStatsView,
    )
    from api.puzzle_details import (
        PuzzleInstanceDetailsView,
        PuzzleOriginalDetailsView,
        InternalPuzzleDetailsView,
        InternalPuzzleDetailsByIdView,
    )
    from api.puzzle_list import (
        InternalPuzzleRenderedResourcesListView,
        PuzzleListView,
        PlayerPuzzleListView,
        GalleryPuzzleListView,
    )
    from api.player_name_register import (
        AdminPlayerNameRegisterView,
        PlayerNameRegisterView,
    )
    from api.player_email_register import PlayerEmailRegisterView
    from api.player_email_login_reset import PlayerEmailLoginResetView
    from api.ping import PingPuzzleView

    from api.tasks import InternalTasksStartView

    # admin views
    from api.puzzle_batch_edit import AdminPuzzleBatchEditView
    from api.player_details_edit import (
        AdminPlayerDetailsEditView,
        AdminPlayerDetailsSlotsView,
    )

    # internal views

    # register the views

    app.add_url_rule(
        "/puzzle/<puzzle_id>/piece/<int:piece>/",
        view_func=PuzzlePieceView.as_view("puzzle-piece-info"),
    )

    app.add_url_rule(
        "/puzzle-pieces/<puzzle_id>/",
        view_func=PuzzlePiecesView.as_view("puzzle-pieces"),
    )
    app.add_url_rule(
        "/puzzle-piece-updates/<stamp>/",
        view_func=PuzzlePieceUpdatesView.as_view("puzzle-piece-updates"),
    )

    # The puzzle-reset route is removed for now in favor of using
    # puzzle-rebuild. Keeping this here in case future updates need to implement
    # a way of resetting a puzzle.
    # app.add_url_rule('/puzzle-reset/',
    #                 view_func=PuzzlePiecesResetView.as_view('puzzle-reset'))
    app.add_url_rule(
        "/puzzle-rebuild/", view_func=PuzzlePiecesRebuildView.as_view("puzzle-rebuild")
    )
    app.add_url_rule(
        "/puzzle-instance/",
        view_func=CreatePuzzleInstanceView.as_view("puzzle-instance"),
    )
    app.add_url_rule(
        "/puzzle-upload/", view_func=PuzzleUploadView.as_view("puzzle-upload")
    )
    app.add_url_rule(
        "/suggest-image/", view_func=SuggestImageView.as_view("suggest-image")
    )

    app.add_url_rule(
        "/current-user-id/", view_func=CurrentUserIDView.as_view("current-user-id")
    )
    app.add_url_rule(
        "/user-details/", view_func=UserDetailsView.as_view("user-details")
    )
    app.add_url_rule(
        "/generate-anonymous-login/",
        view_func=GenerateAnonymousLogin.as_view("generate-anonymous-login"),
    )
    app.add_url_rule(
        "/generate-anonymous-login-by-token/",
        view_func=GenerateAnonymousLoginByToken.as_view(
            "generate-anonymous-login-by-token"
        ),
    )

    app.add_url_rule("/user-logout/", view_func=UserLogoutView.as_view("user-logout"))
    # NGINX rewritten from /puzzle-api/bit/<bitLink>/
    app.add_url_rule(
        "/user-login/<anonymous_login>/", view_func=UserLoginView.as_view("user-login")
    )
    app.add_url_rule(
        "/admin/user-login/", view_func=AdminUserLoginView.as_view("admin-user-login")
    )
    app.add_url_rule("/choose-bit/", view_func=ChooseBitView.as_view("choose-bit"))
    app.add_url_rule("/claim-bit/", view_func=ClaimBitView.as_view("claim-bit"))
    app.add_url_rule("/claim-user/", view_func=ClaimUserView.as_view("claim-user"))
    app.add_url_rule(
        "/puzzle-stats/<puzzle_id>/", view_func=PuzzleStatsView.as_view("puzzle-stats")
    )
    app.add_url_rule(
        "/puzzle-stats/<puzzle_id>/active-player-count/",
        view_func=PuzzleActiveCountView.as_view("puzzle-stats-active-player-count"),
    )
    app.add_url_rule(
        "/player-stats/", view_func=PlayerStatsView.as_view("player-stats")
    )
    app.add_url_rule(
        "/player-ranks/", view_func=PlayerRanksView.as_view("player-ranks")
    )
    app.add_url_rule(
        "/puzzle-instance-details/<puzzle_id>/",
        view_func=PuzzleInstanceDetailsView.as_view("puzzle-instance-details"),
    )
    app.add_url_rule(
        "/puzzle-original-details/<puzzle_id>/",
        view_func=PuzzleOriginalDetailsView.as_view("puzzle-original-details"),
    )
    app.add_url_rule("/puzzle-list/", view_func=PuzzleListView.as_view("puzzle-list"))
    app.add_url_rule(
        "/player-puzzle-list/",
        view_func=PlayerPuzzleListView.as_view("player-puzzle-list"),
    )
    app.add_url_rule(
        "/gallery-puzzle-list/",
        view_func=GalleryPuzzleListView.as_view("gallery-puzzle-list"),
    )
    app.add_url_rule(
        "/player-name-register/",
        view_func=PlayerNameRegisterView.as_view("player-name-register"),
    )
    app.add_url_rule(
        "/player-email-register/",
        view_func=PlayerEmailRegisterView.as_view("player-email-register"),
    )
    app.add_url_rule(
        "/claim-user-by-token/",
        view_func=ClaimUserByTokenView.as_view("claim-user-by-token"),
    )
    app.add_url_rule(
        "/player-email-login-reset/",
        view_func=PlayerEmailLoginResetView.as_view("player-email-login-reset"),
    )
    app.add_url_rule(
        "/ping/puzzle/<puzzle_id>/",
        view_func=PingPuzzleView.as_view("ping-puzzle"),
    )

    # Requires user to press any key to continue
    app.add_url_rule("/post-comment/", view_func=BanishSelf.as_view("banish-self"))

    # admin views
    app.add_url_rule(
        "/admin/puzzle/render/",
        view_func=RenderPuzzlesView.as_view("admin-puzzle-render"),
    )
    app.add_url_rule(
        "/admin/puzzle/batch-edit/",
        view_func=AdminPuzzleBatchEditView.as_view("admin-puzzle-edit"),
    )
    app.add_url_rule(
        "/admin/puzzle/promote-suggested/",
        view_func=AdminPuzzlePromoteSuggestedView.as_view(
            "admin-puzzle-promote-suggested"
        ),
    )
    app.add_url_rule(
        "/admin/puzzle/unsplash-batch/",
        view_func=AdminPuzzleUnsplashBatchView.as_view("admin-puzzle-unsplash-batch"),
    )

    app.add_url_rule(
        "/admin/user/banned/",
        view_func=AdminBannedUserList.as_view("admin-user-banned"),
    )
    app.add_url_rule(
        "/admin/player/details/",
        view_func=AdminPlayerDetailsEditView.as_view("admin-player-details-edit"),
    )
    app.add_url_rule(
        "/admin/player/details/slots/",
        view_func=AdminPlayerDetailsSlotsView.as_view(
            "admin-player-details-slots-edit"
        ),
    )
    app.add_url_rule(
        "/admin/player/name-register/",
        view_func=AdminPlayerNameRegisterView.as_view("admin-player-name-register"),
    )

    # Internal URLs are only accessible for internal applications. This is to
    # support a sqlite client/server model. For now, these are mostly for just
    # being able to write to the database since only the api has database
    # connection with write mode on.

    app.add_url_rule(
        "/internal/puzzle-rendered-resources-list/",
        view_func=InternalPuzzleRenderedResourcesListView.as_view(
            "internal-puzzle-rendered-resources-list"
        ),
    )

    app.add_url_rule(
        "/internal/puzzle/<puzzle_id>/details/",
        view_func=InternalPuzzleDetailsView.as_view("internal-puzzle-details"),
    )
    app.add_url_rule(
        "/internal/pz/<pz_id>/details/",
        view_func=InternalPuzzleDetailsByIdView.as_view(
            "internal-puzzle-details-by-id"
        ),
    )
    app.add_url_rule(
        "/internal/puzzle/<puzzle_id>/pieces/",
        view_func=InternalPuzzlePiecesView.as_view("internal-puzzle-pieces"),
    )
    app.add_url_rule(
        "/internal/puzzle/<puzzle_id>/publish_move/",
        view_func=InternalPuzzlePublishMove.as_view("internal-puzzle-publish-move"),
    )
    app.add_url_rule(
        "/internal/puzzle/<puzzle_id>/files/<file_name>/",
        view_func=InternalPuzzleFileView.as_view("internal-puzzle-file"),
    )
    app.add_url_rule(
        "/internal/puzzle/<puzzle_id>/timeline/",
        view_func=InternalPuzzleTimelineView.as_view("internal-puzzle-timeline"),
    )
    app.add_url_rule(
        "/internal/tasks/<task_name>/start/",
        view_func=InternalTasksStartView.as_view("internal-tasks-start"),
    )
    app.add_url_rule(
        "/internal/user/<user>/details/",
        view_func=InternalUserDetailsView.as_view("internal-user-details"),
    )

    return app


if __name__ == "__main__":
    from api.script import main

    main()
