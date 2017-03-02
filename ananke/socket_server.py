
import json
import os

from autobahn.twisted.websocket import WebSocketServerFactory
from autobahn.twisted.websocket import WebSocketServerProtocol
import treq
from twisted.internet import reactor
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue

from ipgetter import get_ip
import msg
from servicegetters import got_cluster, got_slave, got_notebook, got_hdfs
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
            
        if message == 'remote_socket':
            self.factory.register(self)
            
class NotificationServerFactory(WebSocketServerFactory):
    
    def __init__(self,zpull,host='127.0.0.1',port=settings.WEBSOCKET_PORT):
        WebSocketServerFactory.__init__(self,"ws://"+host+":"+str(port))
        self.clients = []
        self.local_clients = []
        self.subscriber = zpull
        self.subscriber.onPull = self.recv
        
        self.master = tasks.SparkMaster()
        self.slave = tasks.SparkSlave()
        self.pysparknb = tasks.PySparkNoteBook()
        self.snode = tasks.SingleNode()
        self.hdfs = tasks.NameNode()
        
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
            self.master.stop()
            self.broadcast_local('stopped_sparkmaster')
            self.slave.stop()
            self.broadcast_local('stopped_sparkslave')
                
        if job == msg.KILLSLAVE:
            self.slave.stop()
            master_ip = message['ip']
            slave_ip = get_ip()
            req = yield self.update_slaves(master_ip, slave_ip, drop=True)
            self.broadcast_local('stopped_sparkslave')
            
        if job == msg.STARTHDFS:
            okay = yield self.start_hdfs(message['ip'],int(message['slave_count']))
            if not okay:
                self.broadcast_local('start_hdfs_failed')
                
        if job == msg.SLAVECOUNT:
            slave_count_ms = 'slave_count '+str(message['count'])
            self.broadcast_local(slave_count_ms)
            self.broadcast(slave_count_ms)
    
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
        res, okay = yield self.are_we_there_yet(ip,got_cluster,lambda x,ip: " ".join(["master_active",ip]),"master_failed","Spark master")
        returnValue((res,okay))

    @inlineCallbacks 
    def start_slave(self,master_ip,slave_ip):
        if self.slave.start(master_ip, slave_ip):
            res, okay = yield self.wait_slave(slave_ip)
            if okay:
                self.slave.confirm_started()
            self.broadcast_local(res)
            vbox = os.environ.get('VBOX','false')
            #req = yield treq.get('http://'+master_ip+':'+str(settings.APP_PORT)+'/api/reportslave',
            #    params={'ip':[slave_ip], 'drop':['false'], 'virtual':[vbox]}, headers={'Content-Type': ['application/json']})
            req = yield self.update_slaves(master_ip, slave_ip)
            returnValue(True)
        else:
            returnValue(False)
    
    def update_slaves(self, master_ip, slave_ip, drop=False):
        vbox = os.environ.get('VBOX','false')
        if drop:
            drop_par = ['true']
        else:
            drop_par = ['false']
        return treq.get('http://'+master_ip+':'+str(settings.APP_PORT)+'/api/reportslave',
            params={'ip':[slave_ip], 'drop':drop_par, 'virtual':[vbox]}, headers={'Content-Type': ['application/json']})
    
    @inlineCallbacks  
    def wait_slave(self,ip):
        res, okay = yield self.are_we_there_yet(ip,got_slave,lambda x,ip: " ".join(["slave_active",ip]),"slave_failed","Spark slave")
        returnValue((res,okay))

    @inlineCallbacks
    def start_hdfs(self,ip,slave_count):
        if self.hdfs.start(ip):
            res, okay = yield self.wait_hdfs(ip, slave_count)
            if okay:
                self.hdfs.confirm_started()
            self.broadcast_local(res)
            returnValue(True)
        else:
            returnValue(False)

    @inlineCallbacks 
    def wait_hdfs(self, ip, slave_count):
        res, okay = yield self.are_we_there_yet(ip,got_hdfs,lambda x,ip: " ".join(["hdfs_active",ip]),"hdfs_failed","HDFS",max_tries=slave_count*50)
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

