import http.client
import json
import pathlib
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'skills/atlas/scripts'))
from atlaslib.command import parse
from atlaslib.documents import inspect
from atlaslib.finalize import finalize
from atlaslib.graph import index_repository
from atlaslib.handoff import prepare
from atlaslib.labels import set_label
from atlaslib.routing import route, execute

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'skills/atlas/scripts/atlas'


class WorkspaceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name).resolve()
        subprocess.run(['git','init','-q',str(self.root)], check=True)
        (self.root / '.gitignore').write_text('.atlas/\n.env.local\n')
        (self.root / 'decision.md').write_text('# Decision\nStatus: Draft\nOpenAI endpoint and acceptance tests.\n')
        (self.root / 'app.py').write_text('print(1)\n')
        self.graph = index_repository(self.root)

    def test_auto_labels_preserve_review_and_mark_it_stale(self):
        doc = inspect(self.root, self.graph)['documents'][0]
        self.assertEqual(doc['labels']['origin'], 'rule-inferred')
        self.assertIn('ai', doc['labels']['topics'])
        self.assertEqual(doc['labels']['status'], 'draft')
        set_label(self.root,self.graph,'decision.md',topics=['architecture'],status='needs-review')
        (self.root/'decision.md').write_text('# Changed decision\n')
        doc = inspect(self.root,index_repository(self.root))['documents'][0]
        self.assertEqual(doc['labels']['topics'], ['architecture'])
        self.assertEqual(doc['labels']['origin'], 'human-confirmed')
        self.assertEqual(doc['labels']['freshness'], 'stale')

    def test_chat_command_parses_literals_without_shell_execution(self):
        task, options = parse('/codex-atlas TASK="fix $(touch bad)" MODEL=gpt-6-luna RUN=true ALLOW_EDITS=true')
        self.assertEqual(task,'fix $(touch bad)')
        self.assertTrue(options['run'])
        self.assertTrue(options['allow_edits'])
        with self.assertRaises(ValueError): parse('/codex-atlas fix ALLOW_EDITS=true')
        with self.assertRaises(ValueError): parse('/codex-atlas fix RUN=maybe')

    def test_router_bounds_choice_and_never_executes_invalid_result(self):
        response={'status':'completed','output_text':json.dumps({'model':'gpt-6-luna','effort':'low','task_type':'question','reason':'Simple question'}),'usage':{'input_tokens':20}}
        with patch.dict('os.environ',{'OPENAI_API_KEY':'fake-router-key'},clear=True), patch('atlaslib.routing.compatible_models',return_value={'gpt-6-luna'}), patch('atlaslib.routing._call',return_value=response) as api:
            result=route(self.root,self.graph,'Explain app',live=True)
        self.assertEqual(result['status'],'routed')
        payload=api.call_args.args[2]
        self.assertEqual(payload['max_output_tokens'],900)
        self.assertEqual(payload['text']['format']['schema']['properties']['model']['enum'],['gpt-6-luna'])
        response['output_text']=response['output_text'].replace('gpt-6-luna','unknown-model')
        with patch.dict('os.environ',{'OPENAI_API_KEY':'fake-router-key'},clear=True), patch('atlaslib.routing.compatible_models',return_value={'gpt-6-luna'}), patch('atlaslib.routing._call',return_value=response), patch('atlaslib.handoff.prepare') as child:
            result=execute(self.root,self.graph,'Explain app',live=True,run=True)
        self.assertEqual(result['status'],'blocked')
        child.assert_not_called()

    def test_malformed_router_and_missing_key_are_blocked(self):
        with patch.dict('os.environ',{},clear=True):
            self.assertEqual(route(self.root,self.graph,'Explain',live=True)['status'],'blocked')
        with patch.dict('os.environ',{'OPENAI_API_KEY':'fake'},clear=True), patch('atlaslib.routing._call',return_value=[]):
            self.assertEqual(route(self.root,self.graph,'Explain',live=True)['status'],'blocked')

    def test_finalize_is_idempotent_and_refuses_output_symlink(self):
        result=finalize(self.root,'Add a feature')
        memory=(self.root/result['memory']).read_text()
        self.assertEqual(finalize(self.root,'Add a feature'),result)
        self.assertEqual((self.root/result['memory']).read_text(),memory)
        # Recreate the exact output attack without allowing an earlier identity record.
        record=next((self.root/'.atlas/completions').glob('*.json'))
        record.unlink()
        doc=self.root/result['documentation'];doc.unlink()
        outside=self.root.parent/(self.root.name+'-outside')
        self.addCleanup(lambda: outside.unlink(missing_ok=True))
        outside.write_text('preserve')
        doc.symlink_to(outside)
        with self.assertRaises(ValueError):finalize(self.root,'Add a feature')
        self.assertEqual(outside.read_text(),'preserve')

    def test_child_exit_zero_without_completion_is_blocked(self):
        real_run=subprocess.run
        def fake(argv,*args,**kwargs):
            if argv[0]!='codex':return real_run(argv,*args,**kwargs)
            return subprocess.CompletedProcess(argv,0,'','')
        with patch('atlaslib.handoff.subprocess.run',side_effect=fake):
            result=prepare(self.root,self.graph,'Add a feature',run=True,allow_edits=True)
        self.assertEqual(result['result'],'blocked')
        self.assertNotIn('finalize',result)

    def test_server_rejects_cross_origin_and_invalid_payload(self):
        with socket.socket() as probe:
            probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
        child=subprocess.Popen([sys.executable,str(SCRIPT),'--repo',str(self.root),'serve','--port',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.addCleanup(lambda: (child.terminate(),child.wait(timeout=5)))
        for _ in range(60):
            try:
                conn=http.client.HTTPConnection('127.0.0.1',port,timeout=1);conn.request('GET','/api/health');response=conn.getresponse();response.read();conn.close();break
            except OSError:time.sleep(.05)
        else:self.fail('server did not start')
        def request(method,path,body=None,headers=None):
            conn=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
            conn.request(method,path,body,headers or {});response=conn.getresponse();data=response.read();status=response.status;conn.close();return status,data
        status,html=request('GET','/')
        self.assertEqual(status,200)
        import re
        token=re.search(rb'"token":\s*"([^"]+)"',html).group(1).decode()
        self.assertEqual(request('POST','/api/chat','{}',{'Origin':'https://outside.example','X-Atlas-Token':token,'Content-Type':'application/json'})[0],403)
        self.assertEqual(request('GET','/api/health',headers={'Host':'outside.example'})[0],403)
        headers={'Origin':f'http://127.0.0.1:{port}','X-Atlas-Token':token,'Content-Type':'application/json'}
        self.assertEqual(request('POST','/api/chat','[]',headers)[0],400)
        self.assertEqual(request('POST','/api/labels',json.dumps({'path':'../outside.md'}),headers)[0],400)
        status,data=request('POST','/api/labels',json.dumps({'path':'decision.md','topics':['architecture']}),headers)
        self.assertEqual(status,200)
        self.assertEqual(json.loads(data)['labels']['origin'],'human-confirmed')


if __name__=='__main__':unittest.main()
