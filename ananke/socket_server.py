from autobahn.twisted.websocket import WebSocketServerFactory
from autobahn.twisted.websocket import WebSocketServerProtocol

import msg
import settings

from twisted.python import log
from twisted.internet import reactor, protocol

from txzmq import ZmqEndpoint, ZmqFactory, ZmqSubConnection

class NotificationProtocol(WebSocketServerProtocol):

    def onOpen(self):
        self.factory.register(self)

    def onConnect(self, request):
        print("Client connecting: {}".format(request.peer))

    def onMessage(self, payload, isBinary):
        ## echo back message verbatim
        print(payload)
        self.sendMessage(payload, isBinary)

class NotificationServerFactory(WebSocketServerFactory):
    
    def __init__(self,zsub,host='127.0.0.1',port=settings.WEBSOCKET_PORT):
        WebSocketServerFactory.__init__(self,"ws://"+host+":"+str(port))
        self.client = False
        self.subscriber = zsub
        self.subscriber.gotMessage = self.recv
        
        
    def register(self,c):
        self.client = c
        
    def broadcast(self,msg):
        if self.client:
            self.client.sendMessage(str(msg).encode('utf8'))
        
    def recv(self,*args):
        
        job = str(args[0].decode("utf-8").split()[1])
        
        print(job)
        
        if job == msg.WAITMASTER:
            reactor.callInThread(self.wait_master)      
        
    def wait_master(self):
        self.broadcast("master_active")
        
      

if __name__ == '__main__':

    import sys


    zf = ZmqFactory()
    endpoint = ZmqEndpoint("connect", "ipc:///tmp/sock")

    sub = ZmqSubConnection(zf, endpoint)
    sub.subscribe(b'ananke')

    def doPrint(*args):
        print("message received: %r" % (args, ))

    #sub.gotMessage = doPrint


    log.startLogging(sys.stdout)

    ws_factory = NotificationServerFactory(sub)
    ws_factory.protocol = NotificationProtocol





    reactor.listenTCP(settings.WEBSOCKET_PORT, ws_factory)
    reactor.run()