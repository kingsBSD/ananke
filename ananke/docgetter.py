
import json
import pip
import pydoc

from ipgetter import get_ip

def render_doc(doc,ip):
    return {'name': doc.project_name,
        'pypi':'https://pypi.python.org/pypi/'+doc.project_name+'/'+doc.version,
        'local':'http://'+ip+':9000/'+doc.project_name.lower()+'.html'}

def get_docs():
    ip = get_ip()
    return [render_doc(doc,ip) for doc in sorted(pip.get_installed_distributions())]

    