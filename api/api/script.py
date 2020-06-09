"""Api - Puzzle api

Usage: api run [--config <file>]
       api serve [--config <file>]
       api --help
       api --version

Options:
  -h --help         Show this screen.
  --config <file>   Set config file. [default: site.cfg]

Subcommands:
    run     - Start the web server in the foreground. Don't use for production.
    serve   - Starts a daemon web server with Gevent.
"""
from __future__ import print_function
from __future__ import absolute_import
from docopt import docopt

from .app import make_app
from api.tools import loadConfig


def main():
    ""
    args = docopt(__doc__, version="0.0")
    config_file = args["--config"]

    appconfig = loadConfig(config_file)
    cookie_secret = appconfig.get("SECURE_COOKIE_SECRET")

    if args["run"]:
        run(config_file, cookie_secret=cookie_secret)

    if args["serve"]:
        serve(config_file, cookie_secret=cookie_secret)


if __name__ == "__main__":
    main()


def run(config, cookie_secret):
    "Start the web server in the foreground. Don't use for production."
    app = make_app(config=config, cookie_secret=cookie_secret, database_writable=True)

    app.run(
        host=app.config.get("HOSTAPI"),
        port=app.config.get("PORTAPI"),
        use_reloader=True,
    )


def serve(config, cookie_secret):
    from gevent import pywsgi, signal

    app = make_app(config=config, cookie_secret=cookie_secret, database_writable=True)

    host = app.config.get("HOSTAPI")
    port = app.config.get("PORTAPI")

    print(u"serving on {host}:{port}".format(**locals()))
    server = pywsgi.WSGIServer((host, port), app)

    def shutdown():
        app.logger.info("api is being shutdown")

        server.stop(timeout=10)

        exit(signal.SIGTERM)

    signal(signal.SIGTERM, shutdown)
    signal(signal.SIGINT, shutdown)
    server.serve_forever(stop_timeout=10)
