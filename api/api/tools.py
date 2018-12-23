import os

from flask import Config

INITIAL_KARMA = 10
HOUR = 3600 # hour in seconds

def loadConfig(argconfig):
    "Load the config file the same way Flask does which Chill uses."
    config_file = argconfig if argconfig[0] == os.sep else os.path.join(os.getcwd(), argconfig)
    config = Config(os.getcwd())
    config.from_pyfile(config_file)
    return config


def formatPieceMovementString(piece_id, x='', y='', r='', g='', s='', **args):
    if s == None:
        s = ''
    if g == None:
        g = ''
    return u':{piece_id}:{x}:{y}:{r}:{g}:{s}'.format(**locals())

def formatBitMovementString(user_id, x='', y=''):
    return u':{user_id}:{x}:{y}'.format(**locals())

def init_karma_key(redisConnection, puzzle, ip):
    """
    Initialize the karma value and expiration if not set.
    """
    karma_key = 'karma:{puzzle}:{ip}'.format(puzzle=puzzle, ip=ip)
    if redisConnection.setnx(karma_key, INITIAL_KARMA):
        redisConnection.expire(karma_key, HOUR)
    return karma_key

def get_public_karma_points(redisConnection, ip, user, puzzle):
    karma_key = init_karma_key(redisConnection, puzzle, ip)
    points_key = 'points:{user}'.format(user=user)
    recent_points = min(100/2, int(redisConnection.get(points_key) or 0))
    karma = min(100/2, int(redisConnection.get(karma_key)))
    karma = max(0, min(100/2, karma + recent_points))
    return karma
