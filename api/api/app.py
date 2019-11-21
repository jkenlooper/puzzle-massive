import os

from werkzeug.local import LocalProxy
from flask import Flask
from flask import Flask, g, current_app
import sqlite3
import redis

from rq import Queue
from rq.job import Job

from api.flask_secure_cookie import SecureCookie

class API(Flask):
    "API App"


def connect_to_database():
    return sqlite3.connect(current_app.config.get('SQLITE_DATABASE_URI'))

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
        # Enable foreign key support so 'on update' and 'on delete' actions
        # will apply. This needs to be set for each db connection.
        cur = db.cursor()
        cur.execute('pragma foreign_keys = ON;')
        db.commit()

        # Check that journal_mode is set to wal
        result = cur.execute('pragma journal_mode;').fetchone()
        if result[0] != 'wal':
            raise sqlite3.IntegrityError('The pragma journal_mode is not set to wal.')

        cur.close()
    return db

db = LocalProxy(get_db)


def files_loader(*args):
    """
    Loads all the files in each directory as values in a dict with the key
    being the relative file path of the directory.  Updates the value if
    subsequent file paths are the same.
    """
    d = dict()

    def load_files(folder):
        for (dirpath, dirnames, filenames) in os.walk(folder):
            for f in filenames:
                filepath = os.path.join(dirpath, f)
                with open( filepath, 'r' ) as f:
                    key = filepath[len(os.path.commonprefix([root, filepath]))+1:]
                    d[ key ] = f.read()

    for root in args:
        load_files(root)
    return d

def make_app(config=None, **kw):
    app = API('api')

    if config:
        config_file = config if config[0] == os.sep else os.path.join(os.getcwd(), config)
        app.config.from_pyfile(config_file)

    app.config.update(kw)

    # Cookie secret value will be read from app.config.
    # If it does not exist, an exception will be thrown.
    #
    # You can also set the cookie secret in the SecureCookie initializer:
    # secure_cookie = SecureCookie(app, cookie_secret="MySecret")
    #
    app.secure_cookie = SecureCookie(app, cookie_secret=kw['cookie_secret'])

    redisConnection = redis.from_url(app.config.get('REDIS_URI', 'redis://localhost:6379/0/'), decode_responses=True)

    app.queries = files_loader('queries')

    app.cleanupqueue = Queue('puzzle_cleanup', connection=redisConnection)
    app.createqueue = Queue('puzzle_create', connection=redisConnection)

    @app.teardown_appcontext
    def teardown_db(exception):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()

    archive_directory = app.config.get('PUZZLE_ARCHIVE')
    try:
        os.mkdir(archive_directory)
    except OSError:
        # directory already exists
        pass

    resources_directory = app.config.get('PUZZLE_RESOURCES')
    try:
        os.mkdir(resources_directory)
    except OSError:
        # directory already exists
        pass

    # import the views and sockets
    from api.piece import PuzzlePieceView
    from api.publish import PuzzlePiecesMovePublishView, PuzzlePieceTokenView
    from api.pieces import PuzzlePiecesView
    #from api.reset import PuzzlePiecesResetView
    from api.rebuild import PuzzlePiecesRebuildView
    from api.instance import CreatePuzzleInstanceView
    from api.upload import PuzzleUploadView, AdminPuzzlePromoteSuggestedView
    from api.suggest_image import SuggestImageView
    from api.render import RenderPuzzlesView
    from api.user import (
        CurrentUserIDView,
        UserDetailsView,
        GenerateAnonymousLogin,
        GenerateAnonymousLoginByToken,
        UserLogoutView,
        UserLoginView,
        ClaimUserByTokenView,
        ClaimRandomBit,
        SplitPlayer,
        AdminBlockedPlayersList,
        AdminBannedUserList,
        BanishSelf
        )
    from api.bit import BitIconView, ChooseBitView, ClaimBitView, ClaimUserView
    from api.stats import PuzzleStatsView, PlayerRanksView, PuzzleActiveCountView, PlayerStatsView
    from api.puzzle_details import PuzzleInstanceDetailsView, PuzzleOriginalDetailsView
    from api.puzzle_list import PuzzleListView, PlayerPuzzleListView, GalleryPuzzleListView
    from api.player_name_register import AdminPlayerNameRegisterView, PlayerNameRegisterView
    from api.player_email_register import PlayerEmailRegisterView
    from api.player_email_login_reset import PlayerEmailLoginResetView

    # admin views
    from api.puzzle_batch_edit import AdminPuzzleBatchEditView
    from api.player_details_edit import AdminPlayerDetailsEditView, AdminPlayerDetailsSlotsView


    # register the views

    app.add_url_rule('/puzzle/<puzzle_id>/piece/<int:piece>/',
                     view_func=PuzzlePieceView.as_view('puzzle-piece-info'))
    app.add_url_rule('/puzzle/<puzzle_id>/piece/<int:piece>/move/',
                     view_func=PuzzlePiecesMovePublishView.as_view('puzzle-pieces-move'))
    app.add_url_rule('/puzzle/<puzzle_id>/piece/<int:piece>/token/',
                     view_func=PuzzlePieceTokenView.as_view('puzzle-piece-token'))

    app.add_url_rule('/puzzle-pieces/<puzzle_id>/',
                     view_func=PuzzlePiecesView.as_view('puzzle-pieces'))
    # The puzzle-reset route is removed for now in favor of using
    # puzzle-rebuild. Keeping this here in case future updates need to implement
    # a way of resetting a puzzle.
    #app.add_url_rule('/puzzle-reset/',
    #                 view_func=PuzzlePiecesResetView.as_view('puzzle-reset'))
    app.add_url_rule('/puzzle-rebuild/',
                     view_func=PuzzlePiecesRebuildView.as_view('puzzle-rebuild'))
    app.add_url_rule('/puzzle-instance/',
                     view_func=CreatePuzzleInstanceView.as_view('puzzle-instance'))
    app.add_url_rule('/puzzle-upload/', view_func=PuzzleUploadView.as_view('puzzle-upload'))
    app.add_url_rule('/suggest-image/', view_func=SuggestImageView.as_view('suggest-image'))

    app.add_url_rule('/current-user-id/', view_func=CurrentUserIDView.as_view('current-user-id'))
    app.add_url_rule('/user-details/', view_func=UserDetailsView.as_view('user-details'))
    app.add_url_rule('/generate-anonymous-login/',
                     view_func=GenerateAnonymousLogin.as_view('generate-anonymous-login'))
    app.add_url_rule('/generate-anonymous-login-by-token/',
                     view_func=GenerateAnonymousLoginByToken.as_view('generate-anonymous-login-by-token'))

    app.add_url_rule('/split-player/',
                     view_func=SplitPlayer.as_view('split-player'))
    app.add_url_rule('/user-logout/', view_func=UserLogoutView.as_view('user-logout'))
    # NGINX rewritten from /puzzle-api/bit/<bitLink>/
    app.add_url_rule('/user-login/<anonymous_login>/',
                     view_func=UserLoginView.as_view('user-login'))
    app.add_url_rule('/claim-random-bit/',
                     view_func=ClaimRandomBit.as_view('claim-random-bit'))
    app.add_url_rule('/bit-icon/<int:user_id>/',
                     view_func=BitIconView.as_view('bit-icon'))
    app.add_url_rule('/choose-bit/',
                     view_func=ChooseBitView.as_view('choose-bit'))
    app.add_url_rule('/claim-bit/',
                     view_func=ClaimBitView.as_view('claim-bit'))
    app.add_url_rule('/claim-user/',
                     view_func=ClaimUserView.as_view('claim-user'))
    app.add_url_rule('/puzzle-stats/<puzzle_id>/',
                     view_func=PuzzleStatsView.as_view('puzzle-stats'))
    app.add_url_rule('/puzzle-stats/<puzzle_id>/active-player-count/',
                     view_func=PuzzleActiveCountView.as_view('puzzle-stats-active-player-count'))
    app.add_url_rule('/player-stats/',
                     view_func=PlayerStatsView.as_view('player-stats'))
    app.add_url_rule('/player-ranks/',
                     view_func=PlayerRanksView.as_view('player-ranks'))
    app.add_url_rule('/puzzle-instance-details/<puzzle_id>/',
                     view_func=PuzzleInstanceDetailsView.as_view('puzzle-instance-details'))
    app.add_url_rule('/puzzle-original-details/<puzzle_id>/',
                     view_func=PuzzleOriginalDetailsView.as_view('puzzle-original-details'))
    app.add_url_rule('/puzzle-list/',
                     view_func=PuzzleListView.as_view('puzzle-list'))
    app.add_url_rule('/player-puzzle-list/',
                     view_func=PlayerPuzzleListView.as_view('player-puzzle-list'))
    app.add_url_rule('/gallery-puzzle-list/',
                     view_func=GalleryPuzzleListView.as_view('gallery-puzzle-list'))
    app.add_url_rule('/player-name-register/',
                     view_func=PlayerNameRegisterView.as_view('player-name-register'))
    app.add_url_rule('/player-email-register/',
                     view_func=PlayerEmailRegisterView.as_view('player-email-register'))
    app.add_url_rule('/claim-user-by-token/',
                     view_func=ClaimUserByTokenView.as_view('claim-user-by-token'))
    app.add_url_rule('/player-email-login-reset/',
                     view_func=PlayerEmailLoginResetView.as_view('player-email-login-reset'))


    # Requires user to press any key to continue
    app.add_url_rule('/post-comment/',
                     view_func=BanishSelf.as_view('banish-self'))

    # admin views
    app.add_url_rule('/admin/puzzle/render/',
                     view_func=RenderPuzzlesView.as_view('admin-puzzle-render'))
    app.add_url_rule('/admin/puzzle/batch-edit/',
                     view_func=AdminPuzzleBatchEditView.as_view('admin-puzzle-edit'))
    app.add_url_rule('/admin/puzzle/promote-suggested/',
                     view_func=AdminPuzzlePromoteSuggestedView.as_view('admin-puzzle-promote-suggested'))
    app.add_url_rule('/admin/player/blocked/',
                     view_func=AdminBlockedPlayersList.as_view('admin-player-blocked'))
    app.add_url_rule('/admin/user/banned/',
                     view_func=AdminBannedUserList.as_view('admin-user-banned'))
    app.add_url_rule('/admin/player/details/',
                     view_func=AdminPlayerDetailsEditView.as_view('admin-player-details-edit'))
    app.add_url_rule('/admin/player/details/slots/',
                     view_func=AdminPlayerDetailsSlotsView.as_view('admin-player-details-slots-edit'))
    app.add_url_rule('/admin/player/name-register/',
                     view_func=AdminPlayerNameRegisterView.as_view('admin-player-name-register'))

    return app

if __name__ == "__main__":
    from api.script import main
    main()
