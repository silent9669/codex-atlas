import importlib.util
import json
import pathlib
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('package_plugin', pathlib.Path(__file__).resolve().parents[1] / 'scripts/package_plugin.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class PackageTest(unittest.TestCase):
    def test_package_excludes_runtime_and_credentials_and_rebuilds_cleanly(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            for name in package.FILES: (root / name).write_text('{}')
            for name in ('skills/atlas/SKILL.md', 'skills/atlas/.env.local', 'skills/atlas/private.key',
                         '.atlas/workspace.html', '.git/config', '.env', 'skills/atlas/__pycache__/stale.pyc'):
                file = root / name; file.parent.mkdir(parents=True, exist_ok=True); file.write_text('fixture')
            output = package.build(root)
            files = {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}
            self.assertEqual(files, {'.agents/plugins/marketplace.json', 'plugins/codex-atlas/skills/atlas/SKILL.md',
                                    *('plugins/codex-atlas/' + name for name in package.FILES)})
            manifest = json.loads((output / '.agents/plugins/marketplace.json').read_text())
            self.assertEqual(manifest['plugins'][0]['source']['path'], './plugins/codex-atlas')
            (output / 'obsolete').write_text('old')
            package.build(root)
            self.assertFalse((output / 'obsolete').exists())

    def test_source_symlink_cannot_copy_outside_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            for name in package.FILES: (root / name).write_text('{}')
            (root / 'skills').mkdir()
            (root / 'skills/leak.md').symlink_to(root / 'README.md')
            with self.assertRaises(ValueError): package.build(root)
