import json
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ATLAS = ROOT / "skills/atlas/scripts/atlas"


class CliTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = pathlib.Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        for args in (("config", "user.name", "Atlas Test"), ("config", "user.email", "test@example.invalid")):
            subprocess.run(["git", "-C", str(self.repo), *args], check=True)
        (self.repo / "README.md").write_text("# Plan\n[code](app.py)\n")
        (self.repo / "app.py").write_text("def run():\n    return 1\n")
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "fixture"], check=True)

    def run_atlas(self, *args):
        return subprocess.run(["python3", str(ATLAS), "--repo", str(self.repo), *args], text=True, capture_output=True, check=True)

    def test_commands_create_cited_outputs_and_static_report(self):
        indexed = self.run_atlas("index")
        self.assertIn("nodes", json.loads((self.repo / ".atlas/graph.json").read_text()) and indexed.stdout)
        context = self.run_atlas("context", "plan").stdout
        self.assertIn("README.md", context)
        impact = self.run_atlas("impact", "app.py").stdout
        self.assertIn("README.md", impact)
        report = self.run_atlas("report", "--output", ".atlas/report.html").stdout
        self.assertIn("report.html", report)
        self.assertIn("Codex Atlas", (self.repo / ".atlas/report.html").read_text())

    def test_verify_is_blocked_without_reviewed_map_and_stale_after_change(self):
        self.run_atlas("index")
        verification = self.run_atlas("verify").stdout
        self.assertIn("blocked", verification)
        commands = self.repo / ".atlas/commands.json"
        commands.write_text(json.dumps([{"name": "python", "cwd": ".", "argv": ["python3", "-c", "print('ok')"]}]))
        self.assertIn("passed", self.run_atlas("verify", "--commands", str(commands), "--run").stdout)
        (self.repo / "app.py").write_text("def run():\n    return 2\n")
        drift = self.run_atlas("index").stdout
        self.assertIn("Indexed", drift)
        self.assertIn("stale", self.run_atlas("drift").stdout)

    def test_each_command_refreshes_and_supports_json(self):
        self.run_atlas("index")
        (self.repo / "new.py").write_text("def added():\n    return 3\n")
        packet = json.loads(self.run_atlas("context", "added", "--json").stdout)
        self.assertTrue(any(n["path"] == "new.py" for n in packet["nodes"]))
        for args in (("impact", "app.py"), ("explain", "app.py"), ("drift",), ("review", "--changed"), ("verify",)):
            self.assertIn("snapshot_hash", json.loads(self.run_atlas(*args, "--json").stdout))

    def test_verification_persists_failed_blocked_and_redacted_evidence(self):
        commands = self.repo / "commands.json"
        commands.write_text(json.dumps([
            {"name": "missing", "argv": ["atlas-no-such-executable"]},
            {"name": "failed", "argv": ["python3", "-c", "import sys; print('failure'); sys.exit(7)"]},
            {"name": "redact", "argv": ["python3", "-c", "print('Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456 https://example.com/?token=abcdef&x=1')"]},
            {"name": "timeout", "argv": ["python3", "-c", "import time; time.sleep(5)"], "timeout": 0.05}
        ]))
        result = subprocess.run(["python3", str(ATLAS), "--repo", str(self.repo), "verify", "--commands", str(commands), "--run", "--json"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        run = json.loads(result.stdout)
        self.assertEqual([r["result"] for r in run["checks"]], ["blocked", "failed", "passed", "failed"])
        self.assertTrue(all(r["started_at"] and r["ended_at"] and r["snapshot_hash"] for r in run["checks"]))
        stored = "\n".join(p.read_text() for p in (self.repo / ".atlas/evidence").iterdir())
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz123456", stored)
        self.assertNotIn("token=abcdef", stored)
        self.assertIn("[REDACTED]", stored)

    def test_preview_does_not_execute_and_cwd_cannot_escape_repo(self):
        commands = self.repo / "commands.json"
        commands.write_text(json.dumps([{"name": "write", "argv": ["python3", "-c", "open('executed', 'w').close()"]}]))
        self.assertIn("not-run", self.run_atlas("verify", "--commands", str(commands)).stdout)
        self.assertFalse((self.repo / "executed").exists())
        commands.write_text(json.dumps([{"name": "escape", "cwd": "..", "argv": ["python3", "-c", "print('outside')"]}]))
        result = subprocess.run(["python3", str(ATLAS), "--repo", str(self.repo), "verify", "--commands", str(commands), "--run", "--json"], text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout)["checks"][0]["result"], "blocked")

    def test_check_that_changes_source_never_claims_current_pass(self):
        commands = self.repo / "commands.json"
        commands.write_text(json.dumps([{"name": "generator", "argv": ["python3", "-c", "open('app.py','a').write('# generated\\n')"]}]))
        result = subprocess.run(["python3", str(ATLAS), "--repo", str(self.repo), "verify", "--commands", str(commands), "--run", "--json"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["result"], "blocked")
        self.assertEqual(json.loads(result.stdout)["freshness"], "stale")

    def test_scoped_verification_is_attached_to_the_graph(self):
        commands = self.repo / "commands.json"
        commands.write_text(json.dumps([{"name": "syntax", "claim_ids": ["file:app.py"], "behavior": "app.py parses as Python", "argv": ["python3", "-c", "import ast; ast.parse(open('app.py').read())"]}]))
        self.run_atlas("verify", "--commands", str(commands), "--run")
        graph = json.loads(self.run_atlas("index", "--json").stdout)
        edge = next(e for e in graph["edges"] if e["type"] == "verified_by")
        self.assertEqual(edge["source"], "file:app.py")
        runtime = next(n for n in graph["nodes"] if n["id"] == edge["target"])
        self.assertEqual(runtime["result"], "passed")
        self.assertEqual(runtime["freshness"], "current")
        (self.repo / "app.py").write_text("def run():\n    return 8\n")
        updated = json.loads(self.run_atlas("index", "--json").stdout)
        self.assertEqual(next(n for n in updated["nodes"] if n["type"] == "runtime-check")["freshness"], "stale")

    def test_report_cannot_write_outside_repository(self):
        for target in ("/tmp/atlas-outside.html", "../atlas-outside.html"):
            result = subprocess.run(["python3", str(ATLAS), "--repo", str(self.repo), "report", "--output", target], text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
