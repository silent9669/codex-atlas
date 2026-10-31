"""Loopback-only workspace/chat server. OpenAI credentials never enter browser data."""
import hmac
import json
import pathlib
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from . import evidence
from .graph import index_repository
from .graph import digest
from .viewer import render


def workspace(root, launcher, live=None):
    from .documents import inspect
    from .audit import summarize
    graph=evidence.attach(root,index_repository(root))
    graph['workspace']={'documents':inspect(root,graph),'audit':summarize(root,graph),'launcher':str(launcher),'repository_root':str(root),'decisions':[]}
    folder=evidence.storage(root)
    records=[]
    for name in ('decisions','routes'):
        directory=folder/name
        if directory.is_symlink():continue
        records.extend(path for path in directory.glob('*.json') if not path.is_symlink())
    for path in sorted(records,key=lambda p:p.stat().st_mtime,reverse=True)[:5]:
        try:
            record=json.loads(path.read_text())
            if not isinstance(record,dict):continue
            # The workspace needs outcomes and usage, not retained child prompts/argv.
            record={k:record[k] for k in ('kind','task','status','routing','router_model','origin','usage','advisor','reason','snapshot_hash','recorded_at') if k in record}
            record['freshness']='current' if record.get('snapshot_hash')==graph['snapshot']['hash'] else 'stale'
            graph['workspace']['decisions'].append(record)
        except (ValueError,OSError):continue
    if live: graph['workspace']['connection']=live
    return graph


def serve(root, port=8787, env_file=None):
    root=pathlib.Path(root).resolve()
    from .live import runtime_id
    running_id=runtime_id(env_file)
    token=secrets.token_urlsafe(24)
    lock=threading.Lock()
    labels_lock=threading.Lock()
    launcher=pathlib.Path(__file__).resolve().parents[1]/'atlas'
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def authorized_host(self):
            return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
        def send_json(self,status,value):
            encoded=json.dumps(evidence.sanitize(value)).encode()
            self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(encoded)
        def do_GET(self):
            if not self.authorized_host(): return self.send_json(403,{'error':'Invalid workspace host.'})
            if self.path=='/api/health':return self.send_json(200,{'repository_id':digest(str(root)),'runtime_id':running_id,'status':'ready'})
            if self.path not in ('/','/api/graph'):return self.send_json(404,{'error':'Not found.'})
            with labels_lock:
                graph=workspace(root,launcher,{'token':token,'endpoint':'/api/chat'})
            if self.path=='/api/graph':
                if not hmac.compare_digest(self.headers.get('X-Atlas-Token',''),token):return self.send_json(403,{'error':'Workspace token required.'})
                return self.send_json(200,graph)
            # This local HTML contains a session capability, never an OpenAI API key.
            output=evidence.storage(root)/'workspace.html'
            render(graph,output)
            body=output.read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
        def do_POST(self):
            origin=self.headers.get('Origin')
            allowed={f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}
            if not self.authorized_host() or origin not in allowed or not hmac.compare_digest(self.headers.get('X-Atlas-Token',''),token):return self.send_json(403,{'error':'Same-origin workspace request required.'})
            if self.path not in ('/api/chat','/api/labels'):return self.send_json(404,{'error':'Not found.'})
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send_json(415,{'error':'JSON required.'})
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=20000:raise ValueError()
                payload=json.loads(self.rfile.read(size))
                if not isinstance(payload,dict):raise ValueError()
                if self.path=='/api/labels':
                    from .labels import set_label
                    with labels_lock:
                        graph=index_repository(root)
                        return self.send_json(200,set_label(root,graph,payload.get('path',''),payload.get('kind'),payload.get('topics'),payload.get('status')))
                message=payload.get('message','')
                if not isinstance(message,str) or not message.strip() or len(message)>6000:raise ValueError()
            except (ValueError,TypeError,OSError):return self.send_json(400,{'error':'Use a valid document path and labels.' if self.path=='/api/labels' else 'A message of 1–6000 characters is required.'})
            if not lock.acquire(blocking=False):return self.send_json(409,{'error':'Another workspace request is running.'})
            try:
                graph=index_repository(root)
                if message.split()[0]=='/codex-atlas':
                    from .routing import execute
                    from .command import parse
                    task,options=parse(message)
                    result=execute(root,graph,task,live=True,env_file=env_file,**options)
                    reply=result.get('reason') or f"Route: {result['routing']['model']} ({result['routing']['effort']}). {result['routing']['reason']}"
                    if result.get('execution'):
                        execution=result['execution']
                        reply+='\n\nCodex: '+execution['result']+'.'
                        if execution['result']=='not-run':reply+=' Add RUN=true to launch; ALLOW_EDITS=true enables file edits.'
                        if execution.get('reason'):reply+=' '+execution['reason']
                        for title in ('impact','checks','blocked'):
                            items=execution.get('analysis',{}).get(title,[])
                            if items:reply+='\n\n'+title.capitalize()+':\n'+'\n'.join('- '+item for item in items[:8])
                else:
                    from .decision import decide
                    result=decide(root,graph,message,live=True,env_file=env_file)
                    reply=result.get('advisor',{}).get('recommendation') or result.get('reason','No recommendation returned.')
                self.send_json(200,{'reply':reply,'status':result.get('status'),'citations':result.get('evidence_paths',[]),'routing':result.get('routing') if result.get('status') not in {'blocked'} else None,'usage':result.get('usage','unavailable'),'execution':result.get('execution')})
            except (ValueError,OSError):self.send_json(400,{'error':'Workspace request could not complete. Inspect the local environment and source state.'})
            finally:lock.release()
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    print(f'Atlas workspace: http://127.0.0.1:{server.server_port}/',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
