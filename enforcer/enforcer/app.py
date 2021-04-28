from daemonize import Daemonize

from api.tools import loadConfig, get_redis_connection
from enforcer.monitor import monitor


class EnforcerApp:
    "Enforcer App"

    def __init__(self):
        self.pid = f"{__class__.__name__}.pid"

    def start(self):
        daemon = Daemonize(app=__class__.__name__, pid=self.pid, action=self)
        daemon.start()

    def __call__(self):
        monitor(app=self)


def make_app(config_file, **kw):
    app = EnforcerApp()
    config = loadConfig(config_file)
    config.update(kw)

    app.redis_connection = get_redis_connection(config, decode_responses=False)

    return app
