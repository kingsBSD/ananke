
import json

from autobahn.twisted.websocket import WebSocketServerFactory
from autobahn.twisted.websocket import WebSocketServerProtocol

from twisted.internet import reactor, protocol
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue
from twisted.python import log
from txzmq import ZmqEndpoint, ZmqFactory, ZmqPullConnection

import msg
from servicegetters import got_cluster, got_slave, got_notebook
import settings
import tasks

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
        #print(payload)
        
        message = payload.decode("utf-8")
        print(message)
        
        if message == 'local_socket':
            self.factory.register_local(self)


class NotificationServerFactory(WebSocketServerFactory):
    
    def __init__(self,zpull,host='127.0.0.1',port=settings.WEBSOCKET_PORT):
        WebSocketServerFactory.__init__(self,"ws://"+host+":"+str(port))
        self.clients = []
        self.local_clients = []
        self.subscriber = zpull
        self.subscriber.onPull = self.recv
        
        self.master = tasks.MesosMaster()
        self.slave = tasks.MesosSlave()
        self.pysparknb = tasks.PySparkNoteBook()
        self.snode = tasks.SingleNode()
        
    def register(self,c):
        self.clients.append(c)
    
    def unregister(self, c):
        self.clients.remove(c)
        if c in self.local_clients:
            self.local_clients.remove(c)
        
    def register_local(self,c):
        
        if c not in self.local_clients:
            self.local_clients.append(c)
                     
    def broadcast(self,msg):
        print("Sending: "+msg)
        for c in self.clients:
            c.sendMessage(str(msg).encode('utf8'))

    def broadcast_local(self,msg):
        print("Sending Locally: "+msg)
        for c in self.local_clients:
            c.sendMessage(str(msg).encode('utf8'))
        
# https://github.com/crossbario/autobahn-python/tree/master/examples/twisted/websocket/slowsquare        
        
    @inlineCallbacks    
    def recv(self,*args):
                
        message = json.loads(str(args[0][0].decode("utf-8")))
        
        print(message)
        
        job = message.get('msg',False)

        if job == msg.STARTMASTER:
            if self.master.start(message['ip']):
                res, okay = yield self.wait_master(message['ip'])
                self.broadcast_local(res)
                if okay:
                    self.master.confirm_started()
                    slave_okay = yield self.start_slave(message['ip'],message['ip'])
            else:    
                self.broadcast_local('start_master_failed')
                
        if job == msg.STARTSLAVE:
            okay = yield self.start_slave(message['master_ip'], message['slave_ip'])
            if not okay:
                self.broadcast_local('start_slave_failed')
                                    
        if job == msg.STARTPYSPARKNOTEBOOK:
            if self.pysparknb.start(message['ip']):
                res, okay = yield self.wait_notebook(single=False)    
                self.broadcast_local(res)
                if okay:
                    self.pysparknb.confirm_started()
            else:
                self.broadcast_local('start_pysparknotebook_failed')
        
        if job == msg.STARTSINGLENOTEBOOK:
            if self.snode.start():
                res, okay = yield self.wait_notebook(single=True)    
                self.broadcast_local(res)
                if okay:
                    self.snode.confirm_started()
            else:
                self.broadcast_local('start_node_failed')
            
        if job == msg.KILLPYSPARKNOTEBOOK:
            if self.pysparknb.stop():
                self.broadcast_local('stopped_pysparknotebook')
            else:
                self.broadcast_local('couldnt_stop_pysparknotebook')
        
        if job == msg.KILLSINGLENOTEBOOK:
            if self.snode.stop():
                self.broadcast_local('stopped_singlenode')
            else:
                self.broadcast_local('couldnt_stop_singlenode')
        
        if job == msg.KILLMASTER:
            self.slave.stop()
            self.master.stop()
           
            self.broadcast_local('stopped_mesosmaster')
                
        if job == msg.KILLSLAVE:
            self.slave.stop()
            self.broadcast_local('stopped_mesosslave')
    
    @inlineCallbacks
    def wait_notebook(self,single=True):
        if single:
            on_success = lambda x,y: "node_active"
            failure = "node_failed"
        else:
            on_success = lambda x,y: "notebook_active"
            failure = "notebook_failed"
        res, okay = yield self.are_we_there_yet(None,lambda x:got_notebook(),on_success,failure,"Jupyter")     
        returnValue((res,okay))    
            
    
    @inlineCallbacks  
    def wait_master(self,ip):
        res, okay = yield self.are_we_there_yet(ip,got_cluster,lambda x,ip: " ".join(["master_active",ip]),"master_failed","Mesos master")
        returnValue((res,okay))

    @inlineCallbacks 
    def start_slave(self,master_ip,slave_ip):
        if self.slave.start(master_ip, slave_ip):
            res, okay = yield self.wait_slave(slave_ip)
            if okay:
                self.slave.confirm_started()
            self.broadcast_local(res)
            returnValue(True)
        else:
            returnValue(False)
                    
    @inlineCallbacks  
    def wait_slave(self,ip):
        res, okay = yield self.are_we_there_yet(ip,got_slave,lambda sid,x: " ".join(["slave_active",sid]),"slave_failed","Mesos slave")
        returnValue((res,okay))

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
    endpoint = ZmqEndpoint("connect", "ipc:///tmp/sock")

    pull = ZmqPullConnection(zf, endpoint)

    def doPrint(*args):
        print("message received: %r" % (args, ))

    log.startLogging(sys.stdout)

    ws_factory = NotificationServerFactory(pull)
    ws_factory.protocol = NotificationProtocol

    reactor.listenTCP(settings.WEBSOCKET_PORT, ws_factory)
    reactor.run()