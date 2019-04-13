from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
import sys

from collections import OrderedDict

from geventwebsocket import WebSocketServer, Resource

from api.tools import loadConfig
from divulger.app import DivulgeApplication

# Get the args
config_file = sys.argv[1]
config = loadConfig(config_file)


def main():
    ""
    #app = make_app(config=config, cookie_secret=cookie_secret)

    host = config.get("HOSTDIVULGER")
    port = config.get("PORTDIVULGER")

    print(u'serving on {host}:{port}'.format(**locals()))
    #server = pywsgi.WSGIServer((host, port), app)

    server = WebSocketServer(
        (host, port),
        Resource(OrderedDict({
            '^/divulge/.+/': DivulgeApplication,
        })),
        debug=False
    )
    server.serve_forever()


if __name__ == '__main__':
    main()
