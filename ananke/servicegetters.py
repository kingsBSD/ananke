
import json

import requests

import settings

madvertport = str(settings.MESOS_ADVERT_PORT)
notebookport = str(settings.NOTEBOOK_PORT)

def got_cluster(ip):
    try:
        return requests.get("http://"+ip+":8080",timeout=2).status_code == 200
    except:
        return False
    
def got_slave(ip):
    try:
        return json.loads(requests.get("http://"+ip+":"+madvertport+"/state.json",timeout=2).text)['id']
    except:
        return False
    
def got_notebook():
    try:
        return requests.get("http://localhost:"+notebookport,timeout=2).status_code == 200
    except:
        return False