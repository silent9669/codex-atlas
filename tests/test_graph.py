import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "skills/atlas/scripts"
sys.path.insert(0, str(SCRIPTS))
from atlaslib.graph import index_repository


class RepositoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Atlas Test")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], text=True)

    def write(self, path, content):
        dest = self.root / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)

    def fixture(self):
        self.write("docs/decisions/guard.md", "# Grounding\nNumbers need evidence.\n[guard](../../app/guard.py)\n")
        self.write("app/__init__.py", "")
        self.write("app/guard.py", "def ground(value):\n    return value\n")
        self.write("app/api.py", "from .guard import ground\n@router.post('/api/chat')\ndef chat():\n    return ground(1)\n")
        self.write("tests/test_guard.py", "from app.guard import ground\ndef test_grounding():\n    assert ground(1) == 1\n")
        self.write("web/Chat.tsx", "import { ground } from './guard';\nexport function Chat() { return <div>Sources</div>; }\n")
        self.write("web/guard.ts", "export const ground = (n: number) => n;\n")
        self.write("web/chat.test.ts", "import { ground } from './guard';\ntest('grounding', () => { expect(ground(1)).toBe(1); });\n")
        self.write("web/routes.ts", "app.post('/api/pm/chat', handler);\nimport(name);\n")
        self.git("add", ".")
        self.git("commit", "-qm", "Add grounding fixture")

    def test_stable_ast_graph_and_scoped_relationships(self):
        self.fixture()
        first = index_repository(self.root)
        self.assertEqual(first, index_repository(self.root))
        types = {n["type"] for n in first["nodes"]}
        self.assertTrue({"decision", "source", "test", "api", "ui", "commit"} <= types)
        edges = first["edges"]
        self.assertTrue(any(e["type"] == "depends_on" and e["target"] == "file:app/guard.py" for e in edges))
        self.assertTrue(any(e["type"] == "tested_by" and e["origin"] == "parsed" for e in edges))
        self.assertFalse(any(e["type"] == "implements" for e in edges))
        self.assertTrue(all(e["evidence"] and e["explanation"] and e["confidence"] for e in edges))
        self.assertTrue(any(d["kind"] == "dynamic-import" for d in first["diagnostics"]))

    def test_symbol_identity_survives_line_insertion(self):
        self.fixture()
        before = index_repository(self.root)
        self.write("app/guard.py", "\n\ndef ground(value):\n    return value\n")
        after = index_repository(self.root)
        old = next(n for n in before["nodes"] if n.get("symbol") == "ground")
        new = next(n for n in after["nodes"] if n.get("symbol") == "ground")
        self.assertEqual(old["id"], new["id"])
        self.assertNotEqual(old["line"], new["line"])
        self.assertNotEqual(before["snapshot"]["hash"], after["snapshot"]["hash"])

    def test_excludes_secrets_symlinks_and_reports_broken_links(self):
        self.fixture()
        self.write(".env", "API_KEY=not-for-indexing")
        self.write("private.key", "private material")
        self.write("docs/plan.md", "# Plan\n[missing](gone.md)\n")
        (self.root / "leak.py").symlink_to(pathlib.Path(__file__).resolve())
        graph = index_repository(self.root)
        paths = {n["path"] for n in graph["nodes"]}
        self.assertFalse({".env", "private.key", "leak.py"} & paths)
        self.assertTrue(any(d["kind"] == "broken-link" and d["path"] == "docs/plan.md" for d in graph["diagnostics"]))
        self.assertNotIn("not-for-indexing", json.dumps(graph))

    def test_parse_error_is_diagnostic_not_silent_success(self):
        self.fixture()
        self.write("app/broken.py", "def nope(:\n")
        graph = index_repository(self.root)
        self.assertTrue(any(d["kind"] == "parse-error" for d in graph["diagnostics"]))

    def test_history_does_not_connect_unrelated_impact_nodes(self):
        from atlaslib.analysis import impact
        self.fixture()
        self.write("unrelated.py", "def other():\n    pass\n")
        self.git("add", ".")
        self.git("commit", "-qm", "Unrelated change")
        report = impact(index_repository(self.root), "app/guard.py")
        self.assertFalse(any(n["path"] == "unrelated.py" for n in report["indirect"]))


if __name__ == "__main__":
    unittest.main()
