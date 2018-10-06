import os

from flask import Config

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
