
import requests
import subprocess
from concurrent.futures import ThreadPoolExecutor as Pool

from ipgetter import get_ip

def got_cluster(ip):
    try:
        return requests.get("http://"+ip+":5050").status_code == 200
    except:
        return False

#http://stackoverflow.com/questions/2581817/python-subprocess-callback-when-cmd-exits

class MesosMaster:
    
    def __init__(self):
        self.pool = Pool(max_workers=1)
        self.proc = False
        self.running = False
        self.ip = False

    def is_running(self):
        return self.running
    
    def start(self):
        self.ip = get_ip()
        if not self.ip:
            return {'okay': False, 'error':"No active network connection was found."}
        if self.running or got_cluster(self.ip):
            return {'okay': False, 'error':"A Meos master is already running."}
        self.proc = self.pool.submit(subprocess.call, "ananke_mesos_master "+self.ip, shell=True)
        self.running = True
        return {'okay': True, 'ip':self.ip}
    
class MesosSlave:
    
    def __init__(self):
        self.pool = Pool(max_workers=1)
        self.proc = False
        self.running = False
        
    def is_running(self):
        return self.running
        
    def start(self,ip):
        if self.running:
            return {'okay': False, 'error':"A Meos slave is already running."}
        if not got_cluster(ip):
            return {'okay': False, 'error':"Can't find the Meos master."}
        self.proc = self.pool.submit(subprocess.call, "ananke_mesos_slave "+ip, shell=True)
        self.running = True
        return {'okay': True, 'ip':ip}

class SingleNode:
    
    def __init__(self):
        self.running = False
            
    def is_running(self):
        return self.running            