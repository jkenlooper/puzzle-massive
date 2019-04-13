from __future__ import print_function
import json
import time
import re

from gevent import monkey
monkey.patch_all()

from socket import SHUT_RDWR
import redis
from gevent import sleep
from geventwebsocket import WebSocketApplication
from geventwebsocket.exceptions import WebSocketError

redisConnection = redis.from_url('redis://localhost:6379/0/')


# Prevent too many files open errors by limiting the number of possible
# connections that can be open.
MAX_CONNECTIONS = 300

class DivulgeApplication(WebSocketApplication):

    def kill_connection(self, reason):
        #print("kill connection {0}".format(self.ws.handler.client_address))
        self.ws.send(reason)

        # prevent this connection
        self.ws.stream.handler.socket.shutdown(SHUT_RDWR)
        self.ws.stream.handler.socket.close()
        self.ws.close()

    def on_open(self):
        path_match = re.match("/divulge/(.+)/", self.ws.path)
        if not path_match:
            self.kill_connection(404)

        #self.puzzle = path_match.group(1)
        self.ws.handler.environ['puzzle'] = path_match.group(1)

        #print("puzzle: {0}".format(self.ws.handler.environ['puzzle']))
        client_count = len(self.ws.handler.server.clients)
        #print("clients {0}".format(client_count))
        #print "Some client connected!"

        if client_count > MAX_CONNECTIONS:
            # TODO: Unable to get the IP so can't do this: or len(filter(lambda x: x[0] == ws.handler.client_address[0], ws.handler.server.clients.keys())) > MAX_CONNECTIONS_PER_IP:
            #print("Max connections")
            self.kill_connection("MAX")


    def poll_messages(self, pubsub):
        timestamp = time.time()
        while not self.ws.closed:
            # Poll for the move message off of the redis pubsub
            move_message = pubsub.get_message()
            if move_message:
                puzzle_channel = move_message.get('channel')[len('move:'):]
                #print("puzzle_channel: {0}, puzzle: {1}".format(puzzle_channel, self.ws.handler.environ['puzzle']))
                self.broadcast(puzzle_channel, move_message)
            elif (timestamp + 5.0) < time.time():
                break
            sleep(0.001)

    def on_message(self, message):
        """
        parse the message to determine what puzzle and then broadcast that message
        """
        if message is None or message != self.ws.handler.environ['puzzle']:
            #print("message ignored: {0}".format(message))
            return

        # subscribe so
        pubsub = redisConnection.pubsub(ignore_subscribe_messages=True)
        channel = u'move:{0}'.format(self.ws.handler.environ['puzzle'])
        pubsub.subscribe(channel)

        self.poll_messages(pubsub)

        pubsub.unsubscribe(channel)
        pubsub.close()


    def broadcast(self, puzzle, message):
        #print('clients: {0}'.format(len(self.ws.handler.server.clients)))
        # TODO: With redis set the count of total players on the site as well as for each puzzle.

        for (key, client) in list(self.ws.handler.server.clients.items()):
            if client.ws.closed:
                # TODO: I don't think this happens.  This code block hasn't been tested.
                print('remove closed client {0}'.format(key))
                #client.ws.stream.handler.socket.shutdown(SHUT_RDWR)
                #client.ws.stream.handler.socket.close()
                #ws.handler.server.clients.pop(key)
                continue

            # Filter for just the clients for the puzzle
            if client.ws.path.find(puzzle) != -1:
                try:
                    #print("sending message to client: {0}".format(key))
                    client.ws.send(message.get('data'))
                    #print("new activity {0} {1}".format(key, puzzle))
                    #self.ws.handler.environ['last_activity'] = int(time.time())
                except WebSocketError:
                    # Remove dead client

                    print('remove dead client {0}'.format(key))
                    ## Don't use the below commented out methods:
                        #client.ws.stream.handler.socket.shutdown(SHUT_RDWR)
                        #client.ws.stream.handler.socket.close()
                        #client.ws.close()

                    client.ws.close()
                    #self.ws.handler.server.clients.pop(key)

    def on_close(self, reason):
        print("Connection closed! {0} {1}".format(self.ws.handler.environ['puzzle'], self.ws.handler.client_address))

        #channel = u'move:{0}'.format(self.ws.handler.environ['puzzle'])
        #self.ws.handler.environ['pubsub'].unsubscribe(channel)
        #self.ws.handler.environ['pubsub'].close()

