import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'skills/atlas/scripts'))
from atlaslib.journal import summary, recall
from atlaslib.local_env import settings


class JournalTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name).resolve()
        self.store = self.root / '.atlas'
        self.store.mkdir()
        self.graph = {'snapshot': {'files': {'app.py': 'v1', 'docs/atlas/updates/record.md': 'generated'}}}
        self.patch = patch('atlaslib.journal.evidence.storage', return_value=self.store)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def write(self, folder, name, data):
        path = self.store / folder / name
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(data))

    def test_only_relevant_current_successful_memory_is_recalled(self):
        base = {'result':'completed','task':'Fix checkout payment','checks':['unit passed'], 'summary':['Payment works'], 'source_files':{'app.py':'v1'}}
        self.write('completions','a.json',base)
        self.write('completions','b.json',{**base,'task':'Stale checkout','source_files':{'app.py':'v0'}})
        self.write('completions','c.json',{**base,'task':'Failed checkout','result':'blocked'})
        self.assertEqual([m['task'] for m in recall(self.root,self.graph,'checkout')],['Fix checkout payment'])
        self.assertEqual(recall(self.root,self.graph,'unrelated catalog'),[])
        self.assertEqual([m['freshness'] for m in summary(self.root,self.graph)['memories']].count('stale'),1)
        self.graph['snapshot']['files']['app.py']='v2'
        self.assertEqual(recall(self.root,self.graph,'checkout'),[])

    def test_malformed_records_and_prompts_are_not_exposed(self):
        self.write('routes','a.json',{'task':'Read app','execution':{'analysis':{'checks':None},'argv':['SECRET PROMPT'], 'prompt':'SECRET PROMPT','model_route':None}})
        self.write('routes','b.json',{'execution':['bad']})
        self.write('completions','a.json',{'result':'completed','task':[], 'checks':None,'summary':42,'changed':[None]})
        self.write('completions','bad.json',['bad'])
        (self.store/'completions'/'link.json').symlink_to(self.store/'routes'/'a.json')
        data=summary(self.root,self.graph)
        self.assertEqual(len(data['runs']),2)
        self.assertEqual(len(data['memories']),1)
        self.assertNotIn('SECRET PROMPT',json.dumps(data))
        self.assertEqual(recall(self.root,self.graph,'checkout'),[])

    def test_local_environment_shell_wins_and_symlink_is_rejected(self):
        import subprocess
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        (self.root/'.gitignore').write_text('.env.local\n')
        (self.root/'.env.local').write_text('ATLAS_ROUTER_MODEL=local-model\nOPENAI_API_KEY=fake-key\n')
        with patch.dict('os.environ',{'ATLAS_ROUTER_MODEL':'shell-model'},clear=True):
            self.assertEqual(settings(self.root)['ATLAS_ROUTER_MODEL'],'shell-model')
        (self.root/'.env.local').unlink()
        (self.root/'.env.local').symlink_to(self.root/'.gitignore')
        with self.assertRaises(ValueError): settings(self.root)
