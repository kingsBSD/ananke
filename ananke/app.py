import json
from multiprocessing import Process

import time

from flask import Flask, request

import zmq

import settings
import msg

from docgetter import get_docs
from ipgetter import get_ip
from servicegetters import got_cluster, got_slave, got_notebook
from tasks import MesosMaster, MesosSlave, SingleNode, ClusterNoteBook

#master = MesosMaster()
slave = MesosSlave()
cnotebook = ClusterNoteBook()
snode = SingleNode()


    


app = Flask(__name__)

def zocket_send(**kwargs):
    zcontext = zmq.Context()
    socket = zcontext.socket(zmq.PUSH)
    socket.bind("ipc:///tmp/sock")
    socket.send_json(kwargs)
    

@app.route('/')
def root():
    return app.send_static_file('index.html')

@app.route('/api/getdocs')
def all_the_docs():
    return json.dumps({'allthedocs':get_docs()})

@app.route('/api/status')
def status():
    result = {}
    
    ip = get_ip()
    if ip:
        result['network'] = True
        result['ip'] = ip.split('.')
        result['slave_id'] = got_slave(ip)
        result['master_owner'] = got_cluster(ip)
        result['pysparknotebook'] = got_notebook()
        if result['master_owner'] or result['slave_id']:
            result['status'] = 'active'
        else:
            result['status'] = 'dormant'
            
    return json.dumps(result)
    
def valid_ip(ip): 
    try:
        chunks = ip.split('.')
        return len(chunks) == 4 and all([c.isnumeric and 0 <= int(c) <= 255 for c in chunks])
    except:
        return False
    
@app.route('/api/startcluster')
def start_master():
    result = {'okay':False}
    ip = get_ip()
    if not got_cluster(ip):
        if not got_slave(ip):
            zocket_send(msg=msg.STARTMASTER,ip=ip)
            result = {'okay': True, 'ip':ip}
        else:
            result['error'] = "This node is already a Mesos slave."
    else:
        result['error'] = "A Meos master is already running."
    return json.dumps(result)

@app.route('/api/joincluster')
def start_slave():
    result = {'okay':False}
    master_ip = request.args.get('ip', False)
    if valid_ip(master_ip):
        slave_ip = get_ip()
        if got_cluster(master_ip):
            if not got_slave(this_ip):
                zocket_send(msg=msg.STARTSLAVE, master_ip=master_ip, slave_ip=slave_ip)
                result['okay'] = True
            else:
                result['error'] = "This node is already a Mesos slave."
        else:        
            result['error'] = "Can't find the Mesos master."
    else:
        result['error'] = 'Invalid IP address.'
    return json.dumps(result)

@app.route('/api/startclusternotebook')
def start_cluster_notebook():
    ip = request.args.get('ip', False)
    result = cnotebook.start(ip)
    if result['okay']:
        zocket_send(msg=msg.WAITNOTEBOOK)
    return json.dumps(result)

@app.route('/api/ping')
def ping():
    zocket_send(ping="pong")
    return json.dumps({'ping':'pong'})
    
if __name__ == '__main__':

    #sserver.start()

    
    

    #while True:
    #    zsocket.send(bytes("ananke hello",encoding="UTF-8"))
    #    time.sleep(2)
    
    app.run(debug=True)
    
    
    #python3 '-c' 'import pydoc; pydoc.browse(port=9000,open_browser=False)'

    