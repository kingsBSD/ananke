

from os import stat 
import subprocess
from concurrent.futures import ThreadPoolExecutor as Pool

from ipgetter import get_ip
import settings

from servicegetters import got_cluster

#http://stackoverflow.com/questions/2581817/python-subprocess-callback-when-cmd-exits


class Task(object):
    
    def __init__(self):
        self.pool = Pool(max_workers=1)
        self.proc = False
        self.started = False
        self.running = False    

    def run(self,com, args):
        argstr = ' '.join(args)
        try:
            assert (stat(com).st_mode & 2**6) > 0
        except:
            print (com+" is not executable!")
            return False
        try:
            self.proc = self.pool.submit(subprocess.call, ' '.join([com,argstr]), shell=True)
            self.started = True
            return True
        except:
            print (com+" terminated!")
            return False

    def is_running(self):
        return self.running

class SocketServer(Task):

    def __init__(self):
        Task.__init__(self)    

    def start(self):
        Task.run(self,"/usr/bin/python3",["socket_server.py"])

class MesosMaster(Task):
    
    def __init__(self):
        Task.__init__(self)
        self.ip = False

    def start(self):
        if self.started:
            return {'okay': False, 'error':"A Meos master was already started."}
        self.ip = get_ip()
        if not self.ip:
            return {'okay': False, 'error':"No active network connection was found."}
        if self.running or got_cluster(self.ip):
            return {'okay': False, 'error':"A Meos master is already running."}
        if Task.run(self,"/usr/local/bin/ananke_mesos_master",[self.ip]):
            return {'okay': True, 'ip':self.ip}    
        else:
            return {'okay':False, 'error':"Can't start a master."}
                    
class MesosSlave(Task):
    
    def __init__(self):
        Task.__init__(self)
        self.master_ip = False
        
    def start(self,ip):
        if self.started:
            return {'okay': False, 'error':"A Meos slave was already started."}
        if self.running:
            return {'okay': False, 'error':"A Meos slave is already running."}
        if not got_cluster(ip):
            return {'okay': False, 'error':"Can't find the Mesos master."}
        if Task.run(self,"/usr/local/bin/ananke_mesos_slave",[ip,get_ip(),str(settings.MESOS_ADVERT_PORT)]):
            self.master_ip = ip
            return {'okay':True, 'ip':ip}
        else:
            return {'okay':False, 'error':"Can't start a slave."}

class ClusterNoteBook(Task):
    
    def __init__(self):
        Task.__init__(self)
    
    def start(self,ip):
        if self.started:
            return {'okay': False, 'error':"A notebook was already started."}
        if self.running:
            return {'okay': False, 'error':"A notebook is already running."}
        if not got_cluster(ip):
            return {'okay': False, 'error':"Can't find the Mesos master."}
        if Task.run(self,"/usr/local/bin/spark_jupyter_mesos_standalone",[ip]):
            return {'okay':True, 'ip':ip}
        else:
            return {'okay':False, 'error':"Can't start a notebook."}        
        
  
class SingleNode:
    
    def __init__(self):
        self.running = False
            
    def is_running(self):
        return self.running            