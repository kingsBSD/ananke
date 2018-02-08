
import json
import pip
import pydoc

def render_doc(doc):
    return {'name': doc.project_name,
        'pypi':"https://pypi.python.org/pypi/"+doc.project_name+"/"+doc.version,
        'local':"http://localhost:9000/"+doc.project_name.lower()+'.html'}

def get_docs():
    return [render_doc(doc) for doc in sorted(pip.get_installed_distributions())]

    