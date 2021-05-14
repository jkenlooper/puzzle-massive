import signal
import sys
from time import sleep
import logging

from api.tools import loadConfig, get_redis_connection
import enforcer.process


logger = logging.getLogger(__name__)


class EnforcerApp:
    "Enforcer App"

    def __init__(self, config_file, **kw):
        config = loadConfig(config_file)
        config.update(kw)
        logger.setLevel(logging.DEBUG if config["DEBUG"] else logging.INFO)
        self.halt = False
        self.config = config
        self.greenlet_list = []
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
            logger.info(f"new active puzzle {puzzle}")
            self.active_puzzles.add(puzzle)

            try:
                process = enforcer.process.Process(self.config, puzzle)
            except Exception as err:
                self.active_puzzles.remove(puzzle)
                logger.error(err)
            else:
                self.greenlet_list.append(process)

    def start(self):
        logger.info("Starting Enforcer App")
        self.pubsub.psubscribe(
            **{"enforcer_token_request:*": self.handle_active_puzzle}
        )

        while not self.halt:
            pmessage = self.pubsub.get_message()
            if pmessage:
                logger.debug(f"enforcer app got message {pmessage}")

            clean_up_list = False
            for process_glet in self.greenlet_list:
                result = process_glet.switch()
                if result == "DONE":
                    clean_up_list = True
            if clean_up_list:
                new_list = []
                for process_glet in self.greenlet_list:
                    if process_glet.dead:
                        logger.info(f"remove inactive puzzle {process_glet.puzzle}")
                        self.active_puzzles.remove(process_glet.puzzle)
                    else:
                        new_list.append(process_glet)
                self.greenlet_list = new_list

            sleep(0.001)
        self.close()

    def close(self):
        logger.info("Closing Enforcer App")
        self.halt = True
        self.pubsub.punsubscribe("enforcer_token_request:*")
        self.pubsub.close()
        sys.exit(0)

    def cleanup(self, signal, frame):
        self.close()

        logger.debug("exiting")
        sys.exit(0)


def make_app(config_file, **kw):
    app = EnforcerApp(config_file, **kw)

    return app
