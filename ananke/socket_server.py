
import json

from autobahn.twisted.websocket import WebSocketServerFactory
from autobahn.twisted.websocket import WebSocketServerProtocol

import msg
import settings

import requests
from twisted.python import log
from twisted.internet import reactor, protocol
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue

from txzmq import ZmqEndpoint, ZmqFactory, ZmqPullConnection

from servicegetters import got_cluster, got_slave, got_notebook

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
    
    def __init__(self,zpull,host='127.0.0.1',port=settings.WEBSOCKET_PORT):
        WebSocketServerFactory.__init__(self,"ws://"+host+":"+str(port))
        self.clients = []
        self.subscriber = zpull
        self.subscriber.onPull = self.recv
        
        
    def register(self,c):
        self.clients.append(c)
    
    def unregister(self, client):
        for c in self.clients:
            print("unregistered client {}".format(c.peer))
            self.clients.remove(c)
    
          
    def broadcast(self,msg):
        print("Sending: "+msg)
        for c in self.clients:
            c.sendMessage(str(msg).encode('utf8'))
        
# https://github.com/crossbario/autobahn-python/tree/master/examples/twisted/websocket/slowsquare        
        
    @inlineCallbacks    
    def recv(self,*args):
                
        message = json.loads(str(args[0][0].decode("utf-8")))
        
        print(message)
        
        job = message.get('msg',False)
        
        if job == msg.WAITMASTER:
            res, okay = yield self.are_we_there_yet(message['ip'],got_cluster,lambda x,ip: " ".join(["master_active",ip]),"master_failed","Mesos master")
            if okay:
                yield self.launch_slave(message['ip'])
                self.broadcast(res)     
            
        if job == msg.WAITSLAVE:
            res, okay = yield self.are_we_there_yet(message['ip'],got_slave,lambda sid,x: " ".join(["slave_active",sid]),"slave_failed","Mesos slave")
            self.broadcast(res) 
        
        if job == msg.WAITNOTEBOOK:
            res, okay = yield self.are_we_there_yet(None,lambda x:got_notebook(),lambda x,y: "notebook_active","notebook_failed","Jupyter")    
            self.broadcast(res)       

    def launch_slave(self,ip):
        requests.get('http://127.0.0.1:5000/api/joincluster', params={'ip':ip})

    def master_okay(self,x,ip):
        requests.get('http://127.0.0.1:5000/api/joincluster', params={'ip':ip})
        return " ".join(["master_active",ip])

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
            returnValue((on_success(res,param),True))
        else:
            print(debug_fail)
            returnValue((failure,False))
    
                     
if __name__ == '__main__':

    import sys


    zf = ZmqFactory()
    #endpoint = ZmqEndpoint("connect", "ipc:///tmp/sock")
    endpoint = ZmqEndpoint("connect", "ipc:///tmp/sock")

    pull = ZmqPullConnection(zf, endpoint)
    #sub.subscribe(b'ananke')

    def doPrint(*args):
        print("message received: %r" % (args, ))

    log.startLogging(sys.stdout)

    ws_factory = NotificationServerFactory(pull)
    ws_factory.protocol = NotificationProtocol

    reactor.listenTCP(settings.WEBSOCKET_PORT, ws_factory)
    reactor.run()