

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
        try:
            self.proc = self.pool.submit(subprocess.call, ' '.join([com,argstr]), shell=True)
            self.starting = True
            return True
        except:
            print (com+" terminated!")
            return False

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