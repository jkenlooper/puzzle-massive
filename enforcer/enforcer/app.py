from time import sleep
import logging

from api.tools import loadConfig, get_redis_connection
import enforcer.process

# TODO: import multiprocessing-logging to have sub processes show logs

# TODO: use multiprocessing to create a new process for each active puzzle?
# import multiprocessing
from multiprocessing import Pool

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
        logger.debug(f"active puzzle {data}")
        if not data:
            return
        (_, puzzle, _, _, _) = map(int, data.split(":"))
        if puzzle not in self.active_puzzles:
            logger.debug(f"new active puzzle {puzzle}")
            process = enforcer.process.Process(self.config, puzzle)
            self.active_puzzles.add(puzzle)
            if True:
                self.pool.apply_async(
                    process.start,
                    callback=lambda puzzle: self.active_puzzles.remove(puzzle),
                    error_callback=lambda puzzle: self.active_puzzles.remove(puzzle),
                )
            else:
                logger.debug(f"start sync {puzzle}")
                process.start()
                self.active_puzzles.remove(puzzle)
                logger.debug(f"end sync {puzzle}")

    def start(self):
        logger.info(self)
        self.pubsub.subscribe(**{"enforcer_token_request": self.handle_active_puzzle})

        while True:
            pmessage = self.pubsub.get_message()
            if pmessage:
                logger.debug(pmessage)
            # TODO: Set sleep to 0.001 when not developing
            sleep(3)
            logger.debug("sleeping")
        self.pubsub.unsubscribe("enforcer_token_request")
        self.pubsub.close()
        self.pool.close()
        logger.debug("exiting")


def make_app(config_file, **kw):
    app = EnforcerApp(config_file, **kw)

    return app
