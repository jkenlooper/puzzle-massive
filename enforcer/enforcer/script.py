"""Enforcer - Monitor Puzzle Piece Movements

Usage: enforcer start [--config <file>]
       enforcer fg [--config <file>]
       enforcer --help
       enforcer --version

Options:
  -h --help         Show this screen.
  --config <file>   Set config file. [default: site.cfg]

Subcommands:
    start   - Starts the enforcer daemon.
    fg      - Starts the app in the foreground.
"""
import os

from docopt import docopt

from enforcer.app import make_app


def main():
    ""
    args = docopt(__doc__, version="0.0")
    config_file = args["--config"]
    config_file = (
        config_file
        if config_file[0] == os.sep
        else os.path.join(os.getcwd(), config_file)
    )
    app = make_app(config_file)

    if args["start"]:
        # TODO: handle a sys exit stuff to do a graceful shutdown
        app.start()


if __name__ == "__main__":
    main()
