
import requests

from os import stat 
import subprocess
from concurrent.futures import ThreadPoolExecutor as Pool



from ipgetter import get_ip

def got_cluster(ip):
    try:
        return requests.get("http://"+ip+":5050",timeout=2).status_code == 200
    except:
        return False

#http://stackoverflow.com/questions/2581817/python-subprocess-callback-when-cmd-exits


class Task(object):
    
    def __init__(self):
        self.pool = Pool(max_workers=1)
        self.proc = False
        self.running = False    

    def run(self,com, args):
        try:
            assert (stat(com).st_mode & 2**6) > 0
        except:
            print ("Not executable!")
            return False
        try:
            print(' '.join([com,args]))
            self.proc = self.pool.submit(subprocess.call, ' '.join([com,args]), shell=True)
            self.running = True
            return True
        except:
            print ("Terminated")
            return False

    def is_running(self):
        return self.running

class SocketServer(Task):

    def __init__(self):
        Task.__init__(self)    

    def start(self):
        Task.run(self,"/usr/bin/python3","socket_server.py")

class MesosMaster(Task):
    
    def __init__(self):
        Task.__init__(self)
        self.ip = False

    def start(self):
        self.ip = get_ip()
        if not self.ip:
            return {'okay': False, 'error':"No active network connection was found."}
        if self.running or got_cluster(self.ip):
            return {'okay': False, 'error':"A Meos master is already running."}
        if Task.run(self,"/usr/local/bin/ananke_mesos_master",self.ip):
            return {'okay': True, 'ip':self.ip}    
        else:
            return {'okay':False, 'error':"Can't start a master."}
                    
class MesosSlave(Task):
    
    def __init__(self):
        Task.__init__(self)
        
    def start(self,ip):
        if self.running:
            return {'okay': False, 'error':"A Meos slave is already running."}
        if not got_cluster(ip):
            return {'okay': False, 'error':"Can't find the Meos master."}
        if Task.run(self,"/usr/local/bin/ananke_mesos_slave",ip):
            return {'okay':True, 'ip':ip}
        else:
            return {'okay':False, 'error':"Can't start a slave."}


class SingleNode:
    
    def __init__(self):
        self.running = False
            
    def is_running(self):
        return self.running            