#!/usr/bin/env python

import sys
import os.path

from api.tools import loadConfig


def main():
    """
    Prints out the value for a config name in the site.cfg file.
    """
    config_file = sys.argv[1]
    name = sys.argv[2]

    config = loadConfig(config_file)
    value = config[name]

    if isinstance(value, (str, int, float, bool)):
        print(value)
    elif isinstance(value, (list, set)):
        print(" ".join(map(str, value)))


if __name__ == "__main__":
    main()
