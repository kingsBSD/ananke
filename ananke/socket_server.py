from autobahn.twisted.websocket import WebSocketServerFactory
from autobahn.twisted.websocket import WebSocketServerProtocol

import msg
import settings

from twisted.python import log
from twisted.internet import reactor, protocol
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue

from txzmq import ZmqEndpoint, ZmqFactory, ZmqSubConnection

from tasks import got_cluster

def sleep(delay):
    d = Deferred()
    reactor.callLater(delay, d.callback, None)
    return d

class NotificationProtocol(WebSocketServerProtocol):

    def onOpen(self):
        self.factory.register(self)

    def onConnect(self, request):
        print("Client connecting: {}".format(request.peer))

    def connectionLost(self, reason):
        WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)  

    def onMessage(self, payload, isBinary):
        ## echo back message verbatim
        print(payload)
        self.sendMessage(payload, isBinary)

class NotificationServerFactory(WebSocketServerFactory):
    
    def __init__(self,zsub,host='127.0.0.1',port=settings.WEBSOCKET_PORT):
        WebSocketServerFactory.__init__(self,"ws://"+host+":"+str(port))
        self.clients = []
        self.subscriber = zsub
        self.subscriber.gotMessage = self.recv
        
        
    def register(self,c):
        self.clients.append(c)
    
    def unregister(self, client):
        for c in self.clients:
            print("unregistered client {}".format(c.peer))
            self.clients.remove(c)
    
          
    def broadcast(self,msg):
        for c in self.clients:
            c.sendMessage(str(msg).encode('utf8'))
        
# https://github.com/crossbario/autobahn-python/tree/master/examples/twisted/websocket/slowsquare        
        
    @inlineCallbacks    
    def recv(self,*args):
        
        job = str(args[0].decode("utf-8")).split()[1:]
        
        print(job)
        
        if job[0] == msg.WAITMASTER:
            res = yield self.wait_master(job[1])
            self.broadcast(res)
    
    @inlineCallbacks    
    def wait_master(self,ip):
        tries = 0
        master_active = 0
        while tries < 50:
            print("Waiting for the Mesos master...")
            if got_cluster(ip):
                master_active = True
                break;
            tries += 1
            yield sleep(1)
            
        if master_active:
            print("Found Mesos master.")
            returnValue("master_active")
        else:
            print("Mesos master failed to launch.")
            returnValue("master_failed")
            
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