from time import sleep
import logging

from api.tools import loadConfig, get_redis_connection
import enforcer.hotspot


# TODO: use multiprocessing to create a new thread for each active puzzle?
# import multiprocessing

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class EnforcerApp:
    "Enforcer App"
    # channels:
    # enforcer_hotspot
    # enforcer_player_piece_move
    # enforcer_system_group_piece_move

    def __init__(self, config_file, **kw):
        config = loadConfig(config_file)
        config.update(kw)
        self.config = config
        self.redis_connection = get_redis_connection(
            self.config, decode_responses=False
        )

    def start(self):
        logger.info(self)
        pubsub = self.redis_connection.pubsub(ignore_subscribe_messages=False)
        hotspot = enforcer.hotspot.HotSpot(self.redis_connection)
        pubsub.subscribe(enforcer_hotspot=hotspot.handle_message)

        while True:
            pmessage = pubsub.get_message()
            if pmessage:
                logger.debug(pmessage)
            # TODO: Set sleep to 0.001 when not developing
            sleep(3)
            logger.debug("sleeping")
        pubsub.unsubscribe("enforcer_hotspot")
        pubsub.close()
        logger.debug("exiting")


def make_app(config_file, **kw):
    app = EnforcerApp(config_file, **kw)

    return app
