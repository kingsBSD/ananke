
import json

import requests

import settings

def got_cluster(ip):
    try:
        return requests.get("http://"+ip+":5050",timeout=2).status_code == 200
    except:
        return False
    
def got_slave(ip):
    try:
        return json.loads(requests.get("http://"+ip+":"+str(settings.MESOS_ADVERT_PORT)+"/state.json",timeout=2).text)['id']
    except:
        return False
    