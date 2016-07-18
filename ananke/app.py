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
        result['slave_ip'] = got_slave(ip)
        result['master_owner'] = got_cluster(ip)
        result['pysparknotebook'] = got_notebook()
        if result['master_owner'] or result['slave_ip']:
            result['status'] = 'active'
        else:
            result['status'] = 'dormant'
    else:
        result['status'] = 'error'
            
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
            result['error'] = "This node is already a Spark slave."
    else:
        result['error'] = "A Spark master is already running."
    return json.dumps(result)

@app.route('/api/joincluster')
def start_slave():
    result = {'okay':False}
    master_ip = request.args.get('ip', False)
    if valid_ip(master_ip):
        slave_ip = get_ip()
        if got_cluster(master_ip):
            if not got_slave(slave_ip):
                zocket_send(msg=msg.STARTSLAVE, master_ip=master_ip, slave_ip=slave_ip)
                result['okay'] = True
            else:
                result['error'] = "This node is already a Spark slave."
        else:        
            result['error'] = "Can't find the Spark master."
    else:
        result['error'] = 'Missing or invalid IP address.'
    return json.dumps(result)

@app.route('/api/startclusternotebook')
def start_cluster_notebook():
    result = {'okay':False}
    ip = request.args.get('ip', False)
    if valid_ip(ip):
        if got_cluster(ip):
            if not got_notebook():
                zocket_send(msg=msg.STARTPYSPARKNOTEBOOK, ip=ip)
                result['okay'] = True
            else:
                 result['error'] = "A notebook server was already started."
        else:
            result['error'] = "Can't find the Mesos master."
    else:
        result['error'] = 'Missing or invalid IP address.'
    return json.dumps(result)        

@app.route('/api/startsinglenotebook')
def start_single_notebook():
    result = {'okay':False}
    if not got_notebook():
        zocket_send(msg=msg.STARTSINGLENOTEBOOK)
    else:
        result['error'] = "A notebook server was already started."
    return json.dumps(result)

@app.route('/api/stopclusternotebook')
def stop_cluster_notebook():
    result = {'okay':False}
    if got_notebook():
        zocket_send(msg=msg.KILLPYSPARKNOTEBOOK)
        result['okay'] = True
    else:
        result['error'] = "No notebook server is active."
    return json.dumps(result)

@app.route('/api/stopsinglenotebook')
def stop_single_notebook():
    result = {'okay':False}
    if got_notebook():
        zocket_send(msg=msg.KILLSINGLENOTEBOOK)
        result['okay'] = True
    else:
        result['error'] = "No notebook server is active."
    return json.dumps(result)    

@app.route('/api/stopcluster')
def stop_master():
    result = {'okay':False}
    if not got_notebook():
        if got_cluster(get_ip()):
            zocket_send(msg=msg.KILLMASTER)
            result['okay'] = True
        else:
            result['error'] = "No Mesos master is active."            
    else:
        result['error'] = "A notebook server is still active."
    return json.dumps(result)
        
@app.route('/api/leavecluster')
def stop_slave():
    result = {'okay':False}
    if not got_notebook():
        if got_slave(get_ip()):
            zocket_send(msg=msg.KILLSLAVE)
            result['okay'] = True
        else:
            result['error'] = "No Spark slave is active."            
    else:
        result['error'] = "A notebook server is still active."
    return json.dumps(result)        
                
#@app.route('/api/ping')
#def ping():
#    zocket_send(ping="pong")
#    return json.dumps({'ping':'pong'})
    
if __name__ == '__main__':

    app.run(debug=True)
    
