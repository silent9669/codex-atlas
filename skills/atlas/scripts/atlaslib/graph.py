"""Deterministic structural extraction. Semantic relationships are never guessed here."""
import ast
import hashlib
import json
import pathlib
import re
import subprocess
from urllib.parse import unquote, urlsplit

SCHEMA_VERSION = "1.0"
SCRIPT_ROOT = pathlib.Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".atlas", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", "coverage", "ground_truth"}
SECRET = re.compile(r"(^\.env($|\.)|credential|secret|(^|[-_.])token([-_.]|$)|^auth\.json$|^id_(rsa|ed25519)$|\.(pem|key|p12|pfx)$)", re.I)


def digest(data):
    if not isinstance(data, bytes):
        data = json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    return result.stdout.decode("utf-8", "replace") if result.returncode == 0 else ""


def safe_path(root, path):
    relative = pathlib.PurePosixPath(path)
    if relative.is_absolute() or ".." in relative.parts:
        return False
    if any(p in EXCLUDED_PARTS or SECRET.search(p) for p in relative.parts):
        return False
    dest = root / path
    return not any(p.is_symlink() for p in [dest, *dest.parents]) and dest.is_file()


def inventory(root):
    files = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0")
    hashes = {}
    for path in sorted(set(files)):
        if path and safe_path(root, path):
            hashes[path] = digest((root / path).read_bytes())
    commit = git(root, "rev-parse", "HEAD").strip() or None
    return {"commit": commit, "files": hashes, "hash": digest({"commit": commit, "files": hashes})}


def file_type(path):
    lower = path.lower()
    name = pathlib.PurePosixPath(lower).name
    if re.search(r"(^|/)(tests?|__tests__|e2e)/|(^test_.*\.py$)|[.](test|spec)[.]", lower) or name.startswith("test_"):
        return "test"
    if lower.endswith(".md"):
        if any(s in lower for s in ("quyet-dinh/", "decisions/", "adr/")):
            return "decision"
        return "plan" if "plan" in lower else "document"
    if lower.endswith((".tsx", ".jsx")):
        return "ui"
    if any(s in lower for s in ("recording", "replay")):
        return "replay"
    if "eval" in lower:
        return "eval"
    return "source"


def python_data(path, text):
    tree = ast.parse(text, filename=path)
    symbols, imports, routes, diagnostics = [], [], [], []

    def visit(body, prefix=""):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbol = prefix + node.name
                symbols.append({"symbol": symbol, "line": node.lineno, "end_line": node.end_lineno,
                                "type": "test" if node.name.startswith("test_") else "source"})
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in {"get", "post", "put", "patch", "delete", "route", "api_route"}:
                        value = dec.args[0] if dec.args else next((k.value for k in dec.keywords if k.arg == "path"), None)
                        if isinstance(value, ast.Constant) and isinstance(value.value, str):
                            routes.append({"symbol": symbol, "route": value.value, "method": dec.func.attr.upper(), "line": dec.lineno})
                        else:
                            diagnostics.append({"kind": "dynamic-route", "line": dec.lineno, "message": "Nonliteral Python route; prefix/composition requires source review."})
                visit(node.body, symbol + ".")
            elif hasattr(node, "body") and isinstance(node.body, list):
                visit(node.body, prefix)
    visit(tree.body)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend({"module": a.name, "level": 0, "names": [], "line": node.lineno} for a in node.names)
        if isinstance(node, ast.ImportFrom):
            imports.append({"module": node.module or "", "level": node.level, "names": [a.name for a in node.names], "line": node.lineno})
        if isinstance(node, ast.Call) and (getattr(node.func, "id", "") == "__import__" or getattr(node.func, "attr", "") == "import_module"):
            diagnostics.append({"kind": "dynamic-import", "line": node.lineno, "message": "Python runtime import is not resolved."})
    return {"symbols": symbols, "imports": imports, "routes": routes, "diagnostics": diagnostics}


def resolve_python(path, imp, files):
    module = imp["module"].replace(".", "/")
    bases = []
    if imp["level"]:
        parent = pathlib.PurePosixPath(path).parent
        for _ in range(imp["level"] - 1):
            parent = parent.parent
        bases.append(str(parent / module))
    else:
        bases.append(module)
        bases.extend(str(parent / module) for parent in pathlib.PurePosixPath(path).parents if str(parent) != ".")
    for base in bases:
        # `from package import child` may import a submodule instead of __init__.
        for candidate in [*[base + "/" + n + ".py" for n in imp["names"]], base + ".py", base + "/__init__.py"]:
            if candidate in files:
                return candidate
    return None


def index_repository(root, history_limit=20):
    root = pathlib.Path(root).resolve()
    if not git(root, "rev-parse", "--show-toplevel").strip():
        raise ValueError("Atlas requires a Git repository; initialize Git before indexing.")
    if pathlib.Path(git(root, "rev-parse", "--show-toplevel").strip()) != root:
        raise ValueError("--repo must be the repository root.")
    snapshot = inventory(root)
    nodes, edges, diagnostics = {}, {}, []
    records, ts_paths = {}, []

    def node(path, kind, symbol=None, line=1, end_line=None, label=None, identifier=None):
        identifier = identifier or (f"file:{path}" if symbol is None else f"symbol:{path}#{symbol}")
        nodes[identifier] = {"id": identifier, "type": kind, "path": path, "symbol": symbol,
                             "label": label or symbol or path, "line": line, "end_line": end_line,
                             "content_hash": snapshot["files"].get(path)}
        return identifier

    def edge(source, target, kind, path, line, explanation, origin="parsed"):
        identity = digest([source, target, kind, path, line])[:24]
        edges[identity] = {"id": "edge:" + identity, "source": source, "target": target, "type": kind,
                           "origin": origin, "confidence": "observed", "freshness": "current",
                           "evidence": [{"path": path, "line": line, "content_hash": snapshot["files"].get(path)}],
                           "explanation": explanation}

    for path in snapshot["files"]:
        if (root / path).stat().st_size > 1_000_000:
            diagnostics.append({"kind": "size-limit", "path": path, "message": "Hash retained; extraction skipped above 1 MB."})
            continue
        suffix = pathlib.PurePosixPath(path).suffix.lower()
        if suffix not in {".py", ".md", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".yml", ".yaml", ".toml", ".sh"}:
            continue
        identifier = node(path, file_type(path))
        try:
            text = (root / path).read_text(encoding="utf-8")
            if suffix == ".py":
                records[path] = python_data(path, text)
            elif suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}:
                ts_paths.append(path)
            elif suffix == ".md":
                slugs = {}
                in_fence = False
                for line_num, line in enumerate(text.splitlines(), 1):
                    if re.match(r"^\s*(```|~~~)", line):
                        in_fence = not in_fence
                    if in_fence:
                        continue
                    heading = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
                    if heading:
                        label = heading[1]
                        slug = re.sub(r"[^\w\- ]", "", label.lower()).replace(" ", "-")
                        count = slugs.get(slug, 0)
                        slugs[slug] = count + 1
                        section = node(path, file_type(path), slug + (f"-{count}" if count else ""), line_num, label=label)
                        edge(identifier, section, "contains", path, line_num, "Markdown heading belongs to this document.")
                    for match in re.finditer(r"\[[^\]]*\]\(([^\s)]+)(?:\s+[^)]*)?\)", line):
                        link = urlsplit(match[1])
                        if link.scheme or link.netloc or not link.path:
                            continue
                        target_path = (root / path).parent / unquote(link.path)
                        try:
                            target = target_path.resolve().relative_to(root).as_posix()
                        except ValueError:
                            continue
                        if target in snapshot["files"]:
                            edge(identifier, f"file:{target}", "references", path, line_num,
                                 "Explicit local Markdown link; does not establish implementation.", "explicit")
                        else:
                            diagnostics.append({"kind": "broken-link", "path": path, "line": line_num, "target": target, "message": "Local link target is absent or excluded; relationship needs review."})
        except (SyntaxError, UnicodeError) as exc:
            diagnostics.append({"kind": "parse-error", "path": path, "message": str(exc).splitlines()[0]})

    if ts_paths:
        try:
            run = subprocess.run(["node", str(SCRIPT_ROOT / "typescript.cjs")], input=json.dumps({"root": str(root), "paths": ts_paths}), capture_output=True, text=True, timeout=60)
            if run.returncode:
                raise ValueError("TypeScript compiler extractor unavailable; run npm ci at plugin root.")
            records.update(json.loads(run.stdout))
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            diagnostics.append({"kind": "extractor-blocked", "path": "", "message": str(exc)})

    for path, data in records.items():
        file_id = f"file:{path}"
        for item in data["symbols"]:
            kind = "test" if file_type(path) == "test" else item["type"]
            identifier = node(path, kind, item["symbol"], item["line"], item.get("end_line"))
            edge(file_id, identifier, "contains", path, item["line"], "AST declaration belongs to this module.")
        for imp in data["imports"]:
            target = resolve_python(path, imp, snapshot["files"]) if path.endswith(".py") else imp.get("resolved")
            if target and target in nodes_paths(nodes):
                edge(file_id, f"file:{target}", "depends_on", path, imp["line"], "AST import resolves to this module; runtime use is not established.")
                if file_type(path) == "test":
                    edge(f"file:{target}", file_id, "tested_by", path, imp["line"], "Test imports this module; this is a test candidate, not a coverage claim.")
            elif target or imp.get("local") or imp.get("level") or imp.get("module", "").startswith("."):
                diagnostics.append({"kind": "unresolved-import", "path": path, "line": imp["line"], "target": imp.get("module", ""), "message": "Local import not resolved within supported module rules."})
        for route in data["routes"]:
            label = route["method"] + " " + route["route"]
            identifier = node(path, "api", "route:" + label, route["line"], label=label)
            edge(file_id, identifier, "exposes", path, route["line"], "Literal route registration; mounted prefixes and runtime reachability require review.")
        diagnostics.extend({**item, "path": path} for item in data["diagnostics"])

    # Markdown links may point at files whose formats have no extractor.
    for item in list(edges.values()):
        if item["target"].startswith("file:") and item["target"] not in nodes:
            path = item["target"][5:]
            node(path, file_type(path))
    for sha in git(root, "log", f"-{history_limit}", "--format=%H").splitlines():
        paths = git(root, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", sha).splitlines()
        identifier = node("", "commit", sha, label=sha[:12], identifier="commit:" + sha)
        nodes[identifier]["content_hash"] = sha
        for path in paths:
            if f"file:{path}" in nodes:
                edge(f"file:{path}", identifier, "changed_by", path, 1, "Git commit changed this path; historical evidence only.")
    return {"schema_version": SCHEMA_VERSION, "snapshot": snapshot,
            "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
            "edges": sorted(edges.values(), key=lambda e: e["id"]),
            "diagnostics": sorted(diagnostics, key=lambda d: (d.get("path", ""), d.get("line", 0), d["kind"])),
            "limitations": ["Structural extraction does not prove behavior, test coverage, API connectivity or business rules.",
                            "Markdown inline links and ATX headings only; reference links, anchors and rendered MDX are partial.",
                            "Python imports use local module rules; TypeScript uses static module resolution. Aliases from inherited tsconfig are partial.",
                            "Route registrations are literals without router mount composition; generated/file-based routes need review.",
                            "Semantic implements/renders/contradicts links require Codex analysis and human review.",
                            "Excluded secret-like paths, ignored files, symlinks, binaries and ground_truth are not indexed."]}


def nodes_paths(nodes):
    return {item["path"] for item in nodes.values() if item["symbol"] is None}
