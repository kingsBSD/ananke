
from os import stat, environ

from twisted.internet import reactor, protocol

from ipgetter import get_ip
import settings
from servicegetters import got_cluster

class taskProtocol(protocol.ProcessProtocol):
    
    def __init__(self,stopper):
        self.on_stop = stopper
    
    def kill(self):
        self.transport.signalProcess('KILL')

    def processExited(self, reason):
        self.on_stop()
        print(reason)
        
    def processEnded(self, reason):
        self.on_stop()
        print(reason)

class Task(object):
    
    def __init__(self):
        self.proc = False
        self.starting = False
        self.running = False
        self.stopping = False

    def run(self,com, args=[]):
        if self.starting or self.running or self.stopping:
            return False
        argstr = ' '.join(args)
        try:
            assert (stat(com).st_mode & 2**6) > 0
        except:
            print (com+" is not executable!")
            return False
        
        self.proc = taskProtocol(self.confirm_stopped)

        reactor.spawnProcess(self.proc, com, args = [com]+args, env = environ, usePTY=True)
        self.starting = True
        return True

    def stop(self):
        self.stopping = True
        if self.proc:
            self.proc.kill()
            return True
        else:
            return False
    
    def confirm_started(self):
        self.running = True
        self.starting = False
        self.stopping = False

    def confirm_stopped(self):
        self.running = False
        self.starting = False
        self.stopping = False

    def is_running(self):
        return self.running

class SparkMaster(Task):
    
    def __init__(self):
        Task.__init__(self)
        self.ip = False

    def start(self,ip):
        if Task.run(self,"/usr/local/bin/ananke_spark_master",[ip]):
            self.master_ip = ip
            return True
        else:
            return False        
                                
class SparkSlave(Task):
    
    def __init__(self):
        Task.__init__(self)
        self.master_ip = False
        self.ip = False
        
    def start(self,master_ip,slave_ip):
        if Task.run(self,"/usr/local/bin/ananke_spark_slave",[master_ip,slave_ip,str(settings.SPARK_SLAVE_PORT)]):
            self.master_ip = master_ip
            self.ip = slave_ip
            return True
        else:
            return False
        
class PySparkNoteBook(Task):
    
    def __init__(self):
        Task.__init__(self)
    
    def start(self,ip):
        return Task.run(self,"/usr/local/bin/spark_jupyter_standalone",[ip])
                  
class SingleNode(Task):
    
    def __init__(self):
        Task.__init__(self)
            
    def start(self):
        return Task.run(self,"/usr/local/bin/spark_jupyter_single_node")
    
class NameNode(Task):
    
    def __init__(self):
        Task.__init__(self)
            
    def start(self,ip):
        return Task.run(self,"/usr/local/bin/ananke_start_hdfs", [ip])    
