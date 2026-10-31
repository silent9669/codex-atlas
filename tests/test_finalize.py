import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'skills/atlas/scripts'))
from atlaslib.finalize import finalize
from atlaslib.graph import index_repository


class FinalizeTest(unittest.TestCase):
    def test_finalize_writes_project_docs_and_memory_only(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp).resolve()
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            (root / 'README.md').write_text('# Repo\n')
            subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
            subprocess.run(['git', '-C', str(root), 'commit', '-qm', 'fixture'], check=True)
            (root / 'app.py').write_text('print(1)\n')
            result = finalize(root, 'Add the first implementation slice', 'completed', note='validated')
            self.assertTrue((root / result['documentation']).is_file())
            self.assertTrue((root / result['memory']).is_file())
            self.assertIn('codex-atlas routed task', (root / result['documentation']).read_text())
            self.assertIn('Add the first implementation slice', (root / result['memory']).read_text())
            self.assertFalse((root / 'MEMORY.md').exists())


if __name__ == '__main__':
    unittest.main()
