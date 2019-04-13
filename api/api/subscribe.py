from __future__ import print_function
import time

from socket import SHUT_RDWR
import redis
from gevent import sleep
from geventwebsocket.exceptions import WebSocketError
from flask import current_app

redisConnection = redis.from_url('redis://localhost:6379/0/')

pubsub = redisConnection.pubsub(ignore_subscribe_messages=True)

# Prevent too many files open errors by limiting the number of possible
# connections that can be open.
MAX_CONNECTIONS = 200
MAX_CONNECTIONS_FOR_ANON = 100

def puzzle_updates(ws, puzzle):
    """
    Close new connections if already at max connection limit.
    Close current connection if no message received lately.
    """

    def broadcast(puzzle, message):
        print('clients: {0}'.format(len(ws.handler.server.clients)))
        # TODO: With redis set the count of total players on the site as well as for each puzzle.
                
        for (key, client) in ws.handler.server.clients.items():
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
                    print("new activity {0} {1}".format(key, puzzle))
                    ws.handler.environ['last_activity'] = int(time.time())
                except WebSocketError:
                    # Remove dead client
                    
                    #print('remove dead client {0}'.format(key))
                    ## Don't use the below commented out methods:
                        #client.ws.stream.handler.socket.shutdown(SHUT_RDWR)
                        #client.ws.stream.handler.socket.close()
                        #client.ws.close()

                    ws.handler.server.clients.pop(key)

    user = current_app.secure_cookie.get(u'user')

    # TODO: All use the same localhost IP so unable to limit connections to IP
    #print("client {0}".format(ws.handler.client_address))
    #print("client {0}".format(ws.handler.environ))
    #print("client {0}".format(ws.handler.environ['HTTP_X_REAL_IP']))


    # Limit total connections with slightly less if not logged in.  
    max_connection = MAX_CONNECTIONS if user else MAX_CONNECTIONS_FOR_ANON
    max_connection = 100
    if len(ws.handler.server.clients) > max_connection: 
        # TODO: Unable to get the IP so can't do this: or len(filter(lambda x: x[0] == ws.handler.client_address[0], ws.handler.server.clients.keys())) > MAX_CONNECTIONS_PER_IP:
        print("Max connections")

        ws.send("MAX")

        # prevent this connection
        ws.stream.handler.socket.shutdown(SHUT_RDWR)
        ws.stream.handler.socket.close()
        ws.close()
        return

    if False:
        # Initially wait here until a message is received from the socket.  This is
        # to prevent using a socket slot when not needed.
        print("waiting...")
        socket_message = ws.receive()
        #print("socket message: {0}".format(socket_message))
        #if not socket_message:
        if not socket_message or socket_message != '1234abcd':
            print("closing because of no piece movement message")
            ws.close()
            return

    print("connected {0}".format(puzzle))
    channel = u'move:{puzzle}'.format(**locals())
    pubsub.subscribe(channel) # Or could use the path?  print(ws.path)

    # TODO: if no activity on this puzzle; then close all clients.
    ws.handler.environ['last_activity'] = int(time.time())

    # The connection could be closed from inactivity by nginx or other things
    while not ws.closed:
        # Let any of the sockets get the message that is published and
        # broadcast it to all other sockets.
        message = pubsub.get_message()
        if message:
            puzzle_channel = message.get('channel')[len('move:'):]
            broadcast(puzzle_channel, message)

            ## Wait here until a message is recieved from the socket
            #socket_message = ws.receive()
            #print("socket message: {0}".format(socket_message))
            #if not socket_message or socket_message != 'ping':
            #    print("closing because of no message")
            #    ws.close()
            #    #return

        # Sleep for a second. Note that other sockets will also be running in
        # this loop so in theory the more sockets that are connected the less
        # of a delay it will be.
        sleep(5.101)

        # Close all connections for this puzzle if it's stale
        if (ws.handler.environ['last_activity'] + 60) < int(time.time()):
            print("close all stale connections for puzzle {0}".format(puzzle))
            for (key, client) in ws.handler.server.clients.items():
                if client.ws.path.find(puzzle) != -1:
                    ws.handler.server.clients.pop(key)

        if not ws.handler.server.clients.get(ws.handler.client_address):
            ws.stream.handler.socket.shutdown(SHUT_RDWR)
            ws.stream.handler.socket.close()
            print("loop client not in clients list {0}".foramt(puzzle))
            ws.close() 
            break
        print("loop client {0} {1} {2} {3}".format(ws.handler.client_address, puzzle, ws.handler.environ['last_activity'] + 60, int(time.time())))


    print("socket closed {0}".format(puzzle))
    # Unsubscribe from the channel
    pubsub.unsubscribe(channel)

    # Shut down the socket
    #if ws.stream:
    #    ws.stream.handler.socket.shutdown(SHUT_RDWR)
    #    ws.stream.handler.socket.close()
    #if ws and ws.stream:
    #    ws.handler.server.clients.pop(ws.stream.handler.client_address)
