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
from tasks import MesosMaster, MesosSlave, SingleNode, ClusterNoteBook, SocketServer 

master = MesosMaster()
slave = MesosSlave()
cnotebook = ClusterNoteBook()
snode = SingleNode()
sserver = SocketServer()

    


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
    
@app.route('/api/startcluster')
def start_master():
    result = master.start()
    if result['okay']:
        zocket_send(msg=msg.WAITMASTER,ip=result['ip'])
    return json.dumps(result)

@app.route('/api/joincluster')
def start_slave():
    ip = request.args.get('ip', False)
    try:
        chunks = ip.split('.')
        valid = len(chunks) == 4 and all([c.isnumeric and 0 <= int(c) <= 255 for c in chunks])
    except:
        valid = False
    if valid:
        result = slave.start(ip)
        zocket_send(msg=msg.WAITSLAVE,ip=get_ip())
    else:
        result = {'okay':False, 'error':'Invalid IP address.'}
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

    