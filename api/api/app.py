import os

from werkzeug.local import LocalProxy
from flask import Flask
from flask import Flask, g, current_app
#from flask_sockets import Sockets
#from geventwebsocket import WebSocketServer, Resource
import sqlite3
import redis

from rq import Queue
from rq.job import Job
#from worker import redisConnection

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
        c = db.cursor()
        c.execute('pragma foreign_keys = ON;')
        db.commit()
        c.close()
    return db

db = LocalProxy(get_db)


def multiple_directory_files_loader(*args):
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
            for foldername in dirnames:
                load_files(os.path.join(dirpath, foldername))

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

    #sockets = Sockets(app)

    redisConnection = redis.from_url(app.config.get('REDIS_URI', 'redis://localhost:6379/0/'))

    app.queries = multiple_directory_files_loader(os.path.join('api', 'api', 'queries'))

    app.queue = Queue('puzzle_updates', connection=redisConnection)
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
    from api.publish import PuzzlePiecesMovePublishView
    from api.pieces import PuzzlePiecesView
    #from subscribe import puzzle_updates
    from api.reset import PuzzlePiecesResetView
    from api.upload import PuzzleUploadView
    from api.suggest_image import SuggestImageView
    from api.render import RenderPuzzlesView
    from api.user import (
        CurrentUserIDView,
        UserDetailsView,
        GenerateAnonymousLogin,
        UserLogoutView,
        UserLoginView,
        ClaimRandomBit,
        AdminBlockedPlayersList
        )
    from api.bit import BitIconView, ChooseBitView, ClaimBitView

    # admin views
    from api.puzzle_batch_edit import AdminPuzzleBatchEditView


    # register the views

    app.add_url_rule('/puzzle/<puzzle_id>/piece/<int:piece>/',
                     view_func=PuzzlePieceView.as_view('puzzle-piece-info'))
    app.add_url_rule('/puzzle/<puzzle>/piece/<int:piece>/move/',
                     view_func=PuzzlePiecesMovePublishView.as_view('puzzle-pieces-move'))
    app.add_url_rule('/puzzle-pieces/<puzzle_id>/',
                     view_func=PuzzlePiecesView.as_view('puzzle-pieces'))
    app.add_url_rule('/puzzle-reset/',
                     view_func=PuzzlePiecesResetView.as_view('puzzle-reset'))
    app.add_url_rule('/puzzle-upload/', view_func=PuzzleUploadView.as_view('puzzle-upload'))
    app.add_url_rule('/suggest-image/', view_func=SuggestImageView.as_view('suggest-image'))

    app.add_url_rule('/current-user-id/', view_func=CurrentUserIDView.as_view('current-user-id'))
    app.add_url_rule('/user-details/', view_func=UserDetailsView.as_view('user-details'))
    app.add_url_rule('/generate-anonymous-login/',
                     view_func=GenerateAnonymousLogin.as_view('generate-anonymous-login'))
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

    # admin views
    app.add_url_rule('/admin/puzzle/render/',
                     view_func=RenderPuzzlesView.as_view('admin-puzzle-render'))
    app.add_url_rule('/admin/puzzle/batch-edit/',
                     view_func=AdminPuzzleBatchEditView.as_view('admin-puzzle-edit'))
    app.add_url_rule('/admin/player/blocked/',
                     view_func=AdminBlockedPlayersList.as_view('admin-player-blocked'))


    # register the websockets
    #sockets.add_url_rule('/puzzle/<puzzle>/updates/', 'puzzle_updates', puzzle_updates)

    return app

if __name__ == "__main__":
    from api.script import main
    main()
