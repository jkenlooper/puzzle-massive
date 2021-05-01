from time import sleep
import logging
from multiprocessing import Pool

from api.tools import loadConfig, get_redis_connection
import enforcer.process


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class EnforcerApp:
    "Enforcer App"
    # channels:
    # enforcer_active_puzzle
    # enforcer_inactive:{puzzle}
    # enforcer_hotspot:{puzzle}
    # enforcer_player_piece_move
    # enforcer_system_group_piece_move

    def __init__(self, config_file, **kw):
        config = loadConfig(config_file)
        config.update(kw)
        self.config = config
        self.pool = Pool()
        self.pubsub = get_redis_connection(self.config, decode_responses=False).pubsub(
            ignore_subscribe_messages=False
        )
        self.active_puzzles = set()

    def handle_active_puzzle(self, message):
        "message = '{user}:{puzzle}:{piece}:{x}:{y}'"
        data = message.get("data", b"").decode()
        if not data:
            logger.debug(f"handle_active_puzzle no data?")
            return
        (_, puzzle, _, _, _) = map(int, data.split(":"))
        if puzzle not in self.active_puzzles:
            logger.debug(f"new active puzzle {puzzle}")
            self.active_puzzles.add(puzzle)

            def cb(puzzle):
                logger.debug(f"callback {puzzle}")
                self.active_puzzles.remove(puzzle)

            def err_cb(puzzle):
                logger.debug(f"error callback {puzzle}")
                self.active_puzzles.remove(puzzle)

            self.pool.apply_async(
                enforcer.process.start,
                (self.config, puzzle),
                callback=cb,
                error_callback=err_cb,
            )

    def start(self):
        logger.info(self)
        self.pubsub.subscribe(**{"enforcer_token_request": self.handle_active_puzzle})

        while True:
            pmessage = self.pubsub.get_message()
            if pmessage:
                logger.debug(f"enforcer app got message {pmessage}")
            # TODO: Set sleep to 0.001 when not developing
            sleep(0.001)
        self.pubsub.unsubscribe("enforcer_token_request")
        self.pubsub.close()
        self.pool.close()
        logger.debug("exiting")


def make_app(config_file, **kw):
    app = EnforcerApp(config_file, **kw)

    return app
