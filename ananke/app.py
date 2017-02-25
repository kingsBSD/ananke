import json
import os
import time

from klein import Klein
from twisted.web.static import File
import zmq

from db import Database
from docgetter import get_docs
from ipgetter import get_ip
import msg
from servicegetters import got_cluster, got_slave, got_notebook
import settings

app = Klein()
slave_db = Database()

def zocket_send(**kwargs):
    zcontext = zmq.Context()
    socket = zcontext.socket(zmq.PUSH)
    socket.bind("ipc:///tmp/sock")
    socket.send_json(kwargs)
    
@app.route('/', branch=True)
def root(request):
    return File("./static/")

@app.route('/api/getdocs')
def all_the_docs(reques):
    return json.dumps({'allthedocs':get_docs()})

@app.route('/api/status')
def status(request):

    result = {}
    
    result['virtual'] = json.loads(os.environ.get('VBOX','false'))
    
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
def start_master(request):
    result = {'okay':False}
    ip = get_ip()
    if not got_cluster(ip):
        if not got_slave(ip):
            zocket_send(msg=msg.STARTMASTER,ip=ip)
            slave_db.create_db()
            result = {'okay': True, 'ip':ip}
        else:
            result['error'] = "This node is already a Spark slave."
    else:
        result['error'] = "A Spark master is already running."
    return json.dumps(result)

@app.route('/api/joincluster')
def start_slave(request):
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
def start_cluster_notebook(request):
    result = {'okay':False}
    ip = request.args.get('ip', False)
    if valid_ip(ip):
        if got_cluster(ip):
            if not got_notebook():
                slave_db.purge_slaves()
                zocket_send(msg=msg.STARTPYSPARKNOTEBOOK, ip=ip)
                result['okay'] = True
            else:
                 result['error'] = "A notebook server was already started."
        else:
            result['error'] = "Can't find the Spark master."
    else:
        result['error'] = 'Missing or invalid IP address.'
    return json.dumps(result)        

@app.route('/api/startsinglenotebook')
def start_single_notebook(request):
    result = {'okay':False}
    if not got_notebook():
        zocket_send(msg=msg.STARTSINGLENOTEBOOK)
    else:
        result['error'] = "A notebook server was already started."
    return json.dumps(result)

@app.route('/api/stopclusternotebook')
def stop_cluster_notebook(request):
    result = {'okay':False}
    if got_notebook():
        zocket_send(msg=msg.KILLPYSPARKNOTEBOOK)
        result['okay'] = True
    else:
        result['error'] = "No notebook server is active."
    return json.dumps(result)

@app.route('/api/stopsinglenotebook')
def stop_single_notebook(request):
    result = {'okay':False}
    if got_notebook():
        zocket_send(msg=msg.KILLSINGLENOTEBOOK)
        result['okay'] = True
    else:
        result['error'] = "No notebook server is active."
    return json.dumps(result)    

@app.route('/api/stopcluster')
def stop_master(request):
    result = {'okay':False}
    if not got_notebook():
        if got_cluster(get_ip()):
            zocket_send(msg=msg.KILLMASTER)
            slave_db.purge_slaves()
            result['okay'] = True
        else:
            result['error'] = "No Mesos master is active."            
    else:
        result['error'] = "A notebook server is still active."
    return json.dumps(result)
        
@app.route('/api/leavecluster')
def stop_slave(request):
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

@app.route('/api/reportslave', methods=['GET'])
def report_slave(request):
    result = {'okay':False}
    try:
        slave_ip = request.args.get(b'ip', False)[0].decode('utf-8')
    except:
        slave_ip = False
    if valid_ip(slave_ip):
        print("Slave reported: "+slave_ip)
        slave_db.insert_slave(slave_ip)
        result['okay'] = True
    else:
        result['error'] = 'Missing or invalid IP address.'
    return json.dumps(result)        

@app.route('/api/starthdfs')
def start_hdfs(request):
    result = {'okay':True}
    slave_db.get_slaves().addCallback(dump_slaves)
    return json.dumps(result)
    
def dump_slaves(slaves):
    slave_path = os.environ['HADOOP_HOME'] + '/etc/hadoop/slaves'
    with open(slave_path, 'w') as slave_file:
        for s in slaves:
            slave_file.write(s[0]+'\n')

                
@app.route('/api/ping')
def ping(request):
    zocket_send(ping="pong")
    return json.dumps({'ping':'pong'})
    
