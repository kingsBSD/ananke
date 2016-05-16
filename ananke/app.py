import json

from flask import Flask, request

from docgetter import get_docs
from ipgetter import get_ip
from tasks import MesosMaster, MesosSlave, SingleNode

master = MesosMaster()
slave = MesosSlave()
snode = SingleNode()

app = Flask(__name__)

@app.route('/')
def root():
    return app.send_static_file('index.html')

@app.route('/api/getdocs')
def all_the_docs():
    return json.dumps({'allthedocs':get_docs()})

@app.route('/api/status')
def status():
    result = {}
    
    if master.is_running():
        result['status'] = 'master'
    else:
        if slave.is_running():
            result['status'] = 'slave'
        else:
            if snode.is_running():
                result['status'] = 'single'
            else:
                result['status'] = 'dormant'
    ip = get_ip()
    if ip:
        result['network'] = True
        result['ip'] = ip.split('.')
    else:
        result['network'] = False
    return json.dumps(result)
    
@app.route('/api/startcluster')
def start_master():
    result = master.start()
    if result['okay']:
        slave.start(result['ip'])
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
    else:
        result = {'okay':False, 'error':'Invalid IP address.'}
    return json.dumps(result)
    
if __name__ == '__main__':
    app.run(debug=True)
    
    
    #python3 '-c' 'import pydoc; pydoc.browse(port=9000,open_browser=False)'

    