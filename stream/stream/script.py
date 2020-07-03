from gevent import monkey

monkey.patch_all()

import sys
import multiprocessing

import gunicorn.app.base

from stream.app import make_app


def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1


class StreamGunicornBase(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main():
    ""
    # Get the args
    config_file = sys.argv[1]
    app = make_app(config=config_file)

    host = app.config.get("HOSTSTREAM")
    port = app.config.get("PORTSTREAM")

    debug = app.config.get("DEBUG")

    app.logger.info(u"Serving on {host}:{port}".format(**locals()))
    app.logger.info(u"Debug mode is {debug}".format(**locals()))

    options = {
        "loglevel": "info" if not debug else "debug",
        "timeout": 300,  # 5 minutes
        "bind": "%s:%s" % (host, port),
        "worker_class": "gevent",
        "workers": number_of_workers(),
        "reload": debug,
        "preload_app": True,
        # Restart workers after this many requests just in case there are memory leaks
        "max_requests": 1000,
        "max_requests_jitter": 50,
    }
    app = StreamGunicornBase(app, options).run()


if __name__ == "__main__":
    main()
