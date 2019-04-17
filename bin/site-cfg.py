#!/usr/bin/env python

from __future__ import print_function
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

    print(value)

if __name__ == '__main__':
    main()
