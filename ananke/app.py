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
    
def get_request_par(req,par):
    return req.args.get(bytes(par,'utf-8'), False)[0].decode('utf-8')
    
@app.route('/', branch=True)
def root(request):
    return File("./static/")

@app.route('/api/getdocs')
def all_the_docs(reques):
    return json.dumps({'allthedocs':get_docs()})

@app.route('/api/status')
def status(request):

    ip = get_ip()

    result = {}
    
    #result['virtual'] = os.environ.get('VBOX','false') == 'true'
        
    #if result['virtual']:
    #    try:
    #        with open('ip.json', 'r') as ipfile:
    #            result['ext_ip'] = json.loads(ipfile.read())['ip']
    #        result['realip'] = True
    #    except:
    #        result['realip'] = False
    #        result['ext_ip'] = ip
    #else:
    #    result['realip'] = True
              
    #with open('id.json', 'r') as idfile:
    #    result['appid'] = json.loads(idfile.read())['id']
        

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
            slave_db.create_db().addCallback(post_purge)
            result = {'okay': True, 'ip':ip}
        else:
            result['error'] = "This node is already a Spark slave."
    else:
        result['error'] = "A Spark master is already running."
    return json.dumps(result)

def post_purge(*args, **kwargs):
    slave_db.purge_slaves()

@app.route('/api/joincluster')
def start_slave(request):
    result = {'okay':False}
    master_ip = get_request_par(request,'ip')
    print(" MASTER IP ",master_ip)
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
    ip = get_request_par(request,'ip')
    if valid_ip(ip):
        if got_cluster(ip):
            if not got_notebook():
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
            master_ip = get_request_par(request,'ip')
            if master_ip:
                zocket_send(msg=msg.KILLSLAVE, ip=master_ip)
                result['okay'] = True
            else:
                result['error'] = "Missing master_ip."
        else:
            result['error'] = "No Spark slave is active."            
    else:
        result['error'] = "A notebook server is still active."
    return json.dumps(result)        

@app.route('/api/reportslave', methods=['GET'])
def report_slave(request):
    result = {'okay':False}

    slave_ip = get_request_par(request,'ip')

    if valid_ip(slave_ip):
        drop = get_request_par(request,'drop')
        if drop != 'true':
            print("Slave reported: "+slave_ip)
            slave_db.insert_slave(slave_ip).addCallback(slave_db.count_slaves).addCallback(receive_count)
        else:
            print("Dropping slave: "+slave_ip)
            slave_db.drop_slave(slave_ip).addCallback(slave_db.count_slaves).addCallback(receive_count)
        result['okay'] = True
    else:
        result['error'] = 'Missing or invalid IP address.'
    return json.dumps(result)        

def receive_count(count):
    slave_count = count[0][0]
    zocket_send(msg=msg.SLAVECOUNT, count=slave_count)
    
@app.route('/api/writeslaves')
def write_slaves(request):
    slave_db.get_slaves().addCallback(export_slaves)
    return json.dumps({'okay':True})

def export_slaves(slaves):
    slave_path = os.environ['HADOOP_HOME'] + '/etc/hadoop/slaves'
    with open(slave_path, 'w') as slave_file:
        for s in slaves:
            slave_file.write(s[0]+'\n')

@app.route('/api/starthdfs')
def start_hdfs(request):
    result = {'okay':False}
    ip = get_ip()
    if ip:        
        slave_db.get_slaves().addCallback(dump_slaves, ip=ip)
        result = {'okay':True}
    return json.dumps(result)
    
def dump_slaves(slaves,ip=False):
    slave_path = os.environ['HADOOP_HOME'] + '/etc/hadoop/slaves'
    with open(slave_path, 'w') as slave_file:
        for s in slaves:
            slave_file.write(s[0]+'\n')
    zocket_send(msg=msg.STARTHDFS, ip=ip, slave_count=len(slaves))                

@app.route('/api/stophdfs')
def stop_hdfs(request):
    zocket_send(msg=msg.STOPHDFS)
    return json.dumps({'okay':True})

@app.route('/api/hdfsupload')
def hdfs_upload(request):
    name = get_request_par(request,'name')   
    try:
        with open('/home/hdfs/'+name, 'wb') as out:
            out.write(request.args[b'file'][0])
        zocket_send(msg=msg.HDFSUPLOAD, name=name)    
        result = {'okay':True}
    except:
        result = {'okay':False}
        
    return json.dumps(result)
    

@app.route('/api/ping')
def ping(request):
    zocket_send(ping="pong")
    return json.dumps({'ping':'pong'})
    
