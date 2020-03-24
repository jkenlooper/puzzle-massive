from __future__ import division
from past.utils import old_div
import os
import re
import logging

import sqlite3
from flask import Config
import redis

INITIAL_KARMA = 10
HOUR = 3600  # hour in seconds

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def loadConfig(argconfig):
    "Load the config file the same way Flask does which Chill uses."
    config_file = (
        argconfig if argconfig[0] == os.sep else os.path.join(os.getcwd(), argconfig)
    )
    config = Config(os.getcwd())
    config.from_pyfile(config_file)
    return config


def get_db(config):
    db = sqlite3.connect(config.get("SQLITE_DATABASE_URI"))

    # Enable foreign key support so 'on update' and 'on delete' actions
    # will apply. This needs to be set for each db connection.
    cur = db.cursor()
    cur.execute("pragma foreign_keys = ON;")
    db.commit()

    # Check that journal_mode is set to wal
    result = cur.execute("pragma journal_mode;").fetchone()
    if result[0] != "wal":
        raise sqlite3.IntegrityError("The pragma journal_mode is not set to wal.")

    cur.close()

    return db


def get_redis_connection(config, decode_responses=True):
    redis_url = config.get("REDIS_URL")
    if not redis_url:
        raise KeyError("Must set REDIS_URL in site.cfg file.")
    return redis.from_url(redis_url, decode_responses=decode_responses)


def formatPieceMovementString(piece_id, x="", y="", r="", g="", s="", **args):
    if s == None:
        s = ""
    if g == None:
        g = ""
    return u":{piece_id}:{x}:{y}:{r}:{g}:{s}".format(**locals())


def formatBitMovementString(user_id, x="", y=""):
    return u":{user_id}:{x}:{y}".format(**locals())


def init_karma_key(redis_connection, puzzle, ip):
    """
    Initialize the karma value and expiration if not set.
    """
    karma_key = "karma:{puzzle}:{ip}".format(puzzle=puzzle, ip=ip)
    if redis_connection.setnx(karma_key, INITIAL_KARMA):
        redis_connection.expire(karma_key, HOUR)
    return karma_key


def get_public_karma_points(redis_connection, ip, user, puzzle):
    karma_key = init_karma_key(redis_connection, puzzle, ip)
    points_key = "points:{user}".format(user=user)
    recent_points = min(old_div(100, 2), int(redis_connection.get(points_key) or 0))
    karma = min(old_div(100, 2), int(redis_connection.get(karma_key)))
    karma = max(0, min(old_div(100, 2), karma + recent_points))
    return karma


def deletePieceDataFromRedis(redis_connection, puzzle, all_pieces):
    groups = set()
    # TODO: this needs to be one transaction.  There is a chance that the group
    # for a piece may change after it has been added to the groups set.
    for piece in all_pieces:
        pieceFromRedis = redis_connection.hgetall(
            "pc:{puzzle}:{id}".format(puzzle=puzzle, id=piece["id"])
        )
        # Find all the groups for each piece
        groups.add(pieceFromRedis.get("g"))

    # Create a pipe for buffering commands and disable atomic transactions
    # TODO: why disable atomic transaction when deletePieceDataFromRedis?
    pipe = redis_connection.pipeline(transaction=False)

    # Delete all piece data
    for piece in all_pieces:
        pipe.delete("pc:{puzzle}:{id}".format(puzzle=puzzle, id=piece["id"]))

    # Delete all groups
    for g in groups:
        pipe.delete("pcg:{puzzle}:{g}".format(puzzle=puzzle, g=g))

    # Delete Piece Fixed
    pipe.delete("pcfixed:{puzzle}".format(puzzle=puzzle))

    # Delete Piece Stacked
    pipe.delete("pcstacked:{puzzle}".format(puzzle=puzzle))

    # Delete Piece X
    pipe.delete("pcx:{puzzle}".format(puzzle=puzzle))

    # Delete Piece Y
    pipe.delete("pcy:{puzzle}".format(puzzle=puzzle))

    # Remove from the pcupdates sorted set
    pipe.zrem("pcupdates", puzzle)

    pipe.execute()


def check_bg_color(bg_color):
    "Validate the bg_color that was submitted and return a default not valid."
    color_regex = re.compile(".*?#?([a-f0-9]{6}|[a-f0-9]{3}).*?", re.IGNORECASE)
    color_match = color_regex.match(bg_color)
    if color_match:
        return "#{0}".format(color_match.group(1))
    else:
        return "#808080"


strip_chars_regex = re.compile("\s+")


def normalize_name_from_display_name(display_name):
    "Strip out any white-space and lowercase the display_name from NameRegister when storing as name."
    name = display_name.lower()
    name = re.sub(strip_chars_regex, "", name)
    return name


def purge_route_from_nginx_cache(route, PURGEURLLIST):
    """Append route to the purge url list file which will then be picked up by
    the puzzle-massive-cache-purge service."""
    logger.info("Purging {} from nginx cache".format(route))
    f = open(PURGEURLLIST, "a")
    f.write(route + "\n")
    f.close()


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
                with open(filepath, "r") as f:
                    key = filepath[len(os.path.commonprefix([root, filepath])) + 1 :]
                    d[key] = f.read()

    for root in args:
        load_files(root)
    return d
