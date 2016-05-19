from autobahn.twisted.websocket import WebSocketServerFactory
from autobahn.twisted.websocket import WebSocketServerProtocol

import msg
import settings

from twisted.python import log
from twisted.internet import reactor, protocol
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue

from txzmq import ZmqEndpoint, ZmqFactory, ZmqSubConnection

from servicegetters import got_cluster, got_slave

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
            res = yield self.are_we_there_yet(job[1],got_cluster,lambda x: "master_active","master_failed","Mesos master")
            
        if job[0] == msg.WAITSLAVE:
            res = yield self.are_we_there_yet(job[1],got_slave,lambda sid: " ".join(["slave_active",sid]),"slave_failed","Mesos slave")
            
        self.broadcast(res)       

    @inlineCallbacks
    def are_we_there_yet(self,param,tester,on_success,failure,wait_for=False,max_tries=50):
        tries = 0
        res = False
        if wait_for:
            debug_str = "Waiting for " + wait_for + "..."
            debug_done = "Found " + wait_for
            debug_fail = "Can't find " + wait_for
        else:
            debug_str = "Waiting..."
            debug_done = "Found."
            debug_fail = "Not found."
        while tries < max_tries:
            print(debug_str)
            res = tester(param)
            if res:
                break
            tries += 1
            yield sleep(1)
    
        if res:
            print(debug_done)
            returnValue(on_success(res))
        else:
            print(debug_fail)
            returnValue(failure)
    
                     
if __name__ == '__main__':

    import sys


    zf = ZmqFactory()
    endpoint = ZmqEndpoint("connect", "ipc:///tmp/sock")

    sub = ZmqSubConnection(zf, endpoint)
    sub.subscribe(b'ananke')

    def doPrint(*args):
        print("message received: %r" % (args, ))

    log.startLogging(sys.stdout)

    ws_factory = NotificationServerFactory(sub)
    ws_factory.protocol = NotificationProtocol

    reactor.listenTCP(settings.WEBSOCKET_PORT, ws_factory)
    reactor.run()