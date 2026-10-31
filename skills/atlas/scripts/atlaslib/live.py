"""Start or reuse the loopback workspace without blocking the caller."""
import json
import os
import pathlib
import socket
import subprocess
import time
import urllib.request
import webbrowser
from . import evidence
from .graph import digest


def runtime_id(env_file=None):
    folder=pathlib.Path(__file__).parent
    return digest({'files':{p.name:digest(p.read_bytes()) for p in folder.iterdir() if p.suffix in {'.py','.html','.css','.js'}},
                   'env_file':str(env_file) if env_file else None, 'environment_key':bool(os.environ.get('OPENAI_API_KEY'))})


def start(root, env_file=None, open_browser=False):
    folder=evidence.storage(root);record=folder/'server.json'
    previous=json.loads(record.read_text()) if record.exists() and not record.is_symlink() else {}
    repo_id=digest(str(root))
    if previous.get('port'):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{int(previous['port'])}/api/health",timeout=1) as response:
                health=json.loads(response.read())
            if health.get('repository_id')==repo_id and health.get('runtime_id')==runtime_id(env_file):
                url=f"http://127.0.0.1:{previous['port']}/"
                if open_browser:webbrowser.open(url)
                return {'kind':'workspace','url':url,'status':'running','reused':True}
        except (OSError,ValueError):pass
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    script=pathlib.Path(__file__).resolve().parents[1]/'atlas'
    argv=['python3',str(script),'--repo',str(root),'serve','--port',str(port)]
    if env_file:argv+=['--env-file',str(env_file)]
    log=folder/'server.log'
    if log.is_symlink():raise ValueError('Refusing symlinked server log.')
    with log.open('ab') as output:
        child=subprocess.Popen(argv,cwd=root,stdout=output,stderr=output,start_new_session=True)
    log.chmod(0o600)
    for _ in range(30):
        if child.poll() is not None:raise ValueError('Atlas workspace server failed to start; inspect .atlas/server.log.')
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health',timeout=.2) as response:
                health=json.loads(response.read())
            if health.get('repository_id')==repo_id:break
        except (OSError,ValueError):time.sleep(.1)
    else:
        child.terminate();raise ValueError('Atlas workspace did not become ready.')
    evidence.write_json(record,{'pid':child.pid,'port':port,'repository_id':repo_id})
    url=f'http://127.0.0.1:{port}/'
    if open_browser:webbrowser.open(url)
    return {'kind':'workspace','url':url,'status':'running','reused':False}
