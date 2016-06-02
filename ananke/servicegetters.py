
import json

import requests

import settings

madvertport = str(settings.SPARK_SLAVE_PORT)
notebookport = str(settings.NOTEBOOK_PORT)

def got_cluster(ip):
    try:
        return requests.get("http://"+ip+":8080",timeout=2).status_code == 200
    except:
        return False
    
def got_slave(ip):
    try:
        if requests.get("http://"+ip+":8081",timeout=2).status_code == 200:
            return ip
        else:
            return False
    except:
        return False
    
def got_notebook():
    try:
        return requests.get("http://localhost:"+notebookport,timeout=2).status_code == 200
    except:
        return False