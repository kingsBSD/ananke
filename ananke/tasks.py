
from os import stat, environ

from twisted.internet import reactor, protocol

from ipgetter import get_ip
import settings
from servicegetters import got_cluster

class taskProtocol(protocol.ProcessProtocol):
        
    def kill(self):
        self.transport.signalProcess('KILL')

class Task(object):
    
    def __init__(self):
        self.proc = False
        self.starting = False
        self.running = False
        self.stopping = False

    def run(self,com, args):
        if self.starting or self.running:
            return False
        argstr = ' '.join(args)
        try:
            assert (stat(com).st_mode & 2**6) > 0
        except:
            print (com+" is not executable!")
            return False
        
        self.proc = taskProtocol()
        reactor.spawnProcess(self.proc, com, args = [com]+args, env = environ, usePTY=True)
        
        return True
        
    def confirm_started(self):
        self.running = True
        self.starting = False

    def confirm_stopped(self):
        self.running = False
        self.stopping = False

    def is_running(self):
        return self.running

class MesosMaster(Task):
    
    def __init__(self):
        Task.__init__(self)
        self.ip = False

    def start(self,ip):
        if Task.run(self,"/usr/local/bin/ananke_mesos_master",[ip]):
            self.master_ip = ip
            return True
        else:
            return False        
                            
class MesosSlave(Task):
    
    def __init__(self):
        Task.__init__(self)
        self.master_ip = False
        self.ip = False
        
    def start(self,master_ip,slave_ip):
        if Task.run(self,"/usr/local/bin/ananke_mesos_slave",[master_ip,slave_ip,str(settings.MESOS_ADVERT_PORT)]):
            self.master_ip = master_ip
            self.ip = slave_ip
            return True
        else:
            return False
        
class PySparkNoteBook(Task):
    
    def __init__(self):
        Task.__init__(self)
    
    def start(self,ip):
        return Task.run(self,"/usr/local/bin/spark_jupyter_mesos_standalone",[ip])
         
class SingleNode:
    
    def __init__(self):
        self.running = False
            
    def is_running(self):
        return self.running            