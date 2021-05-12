import signal
import sys
from time import sleep
import logging
from multiprocessing import Pool
import atexit

from api.tools import loadConfig, get_redis_connection
import enforcer.process


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class EnforcerApp:
    "Enforcer App"

    def __init__(self, config_file, **kw):
        config = loadConfig(config_file)
        config.update(kw)
        self.halt = False
        self.config = config
        self.pool = Pool()
        self.pubsub = get_redis_connection(self.config, decode_responses=False).pubsub(
            ignore_subscribe_messages=False
        )
        self.active_puzzles = set()

        signal.signal(signal.SIGINT, self.cleanup)

    def handle_active_puzzle(self, message):
        "message = '{user}:{piece}:{x}:{y}'"
        channel = message.get("channel", b"").decode()
        puzzle = int(channel.split(":")[1])
        if puzzle not in self.active_puzzles:
            logger.debug(f"new active puzzle {puzzle}")
            self.active_puzzles.add(puzzle)

            def cb(puzzle):
                logger.debug(f"callback for puzzle: {puzzle}")
                self.active_puzzles.remove(int(puzzle))
                atexit.unregister(halt_process)

            def err_cb(message):
                logger.error(f"error callback for puzzle: {puzzle}")
                logger.error(message)
                self.active_puzzles.remove(puzzle)
                atexit.unregister(halt_process)

            def halt_process():
                cb(puzzle)

            # TODO: Switch to starting a new Process instead of using a Pool
            self.pool.apply_async(
                enforcer.process.start,
                (self.config, puzzle),
                callback=cb,
                error_callback=err_cb,
            )
            atexit.register(halt_process)

    def start(self):
        logger.info(self)
        self.pubsub.psubscribe(
            **{"enforcer_token_request:*": self.handle_active_puzzle}
        )

        while not self.halt:
            pmessage = self.pubsub.get_message()
            if pmessage:
                logger.debug(f"enforcer app got message {pmessage}")
            sleep(0.001)

    def close(self):
        logger.debug("closing app")
        self.halt = True
        self.pubsub.punsubscribe("enforcer_token_request:*")
        self.pubsub.close()
        self.pool.close()
        sys.exit(0)

    def cleanup(self, signal, frame):
        self.close()

        logger.debug("exiting")
        sys.exit(0)


def make_app(config_file, **kw):
    app = EnforcerApp(config_file, **kw)

    return app
