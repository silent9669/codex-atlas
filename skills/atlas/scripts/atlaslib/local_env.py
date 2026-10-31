"""Read repository-local credentials; never alter global configuration."""
import os
import pathlib
import re
import subprocess


def settings(root, env_file=None):
    values = {key: os.environ[key] for key in ('OPENAI_API_KEY', 'ATLAS_ADVISOR_MODEL', 'ATLAS_CODEX_MODEL', 'ATLAS_ROUTER_MODEL', 'ATLAS_EXECUTION_MODELS') if key in os.environ}
    if not env_file:
        candidate = root / '.env.local'
        if not candidate.exists() and not candidate.is_symlink(): return values
        env_file = '.env.local'
    file = pathlib.Path(env_file)
    if not file.is_absolute():
        file = root / file
    if file.is_symlink() or not file.resolve().is_relative_to(root) or not file.is_file():
        raise ValueError('--env-file must be a local file inside the repository.')
    relative = file.resolve().relative_to(root).as_posix()
    ignored = subprocess.run(['git', '-C', str(root), 'check-ignore', '--quiet', relative]).returncode == 0
    tracked = subprocess.run(['git', '-C', str(root), 'ls-files', '--error-unmatch', relative], capture_output=True).returncode == 0
    if tracked or not ignored:
        raise ValueError('--env-file must be untracked and Git-ignored before credentials can be loaded.')
    if file.stat().st_size > 16384:
        raise ValueError('Local environment file exceeds 16 KB.')
    for line in file.read_text().splitlines():
        match = re.fullmatch(r'\s*(?:export\s+)?(OPENAI_API_KEY|ATLAS_ADVISOR_MODEL|ATLAS_CODEX_MODEL|ATLAS_ROUTER_MODEL|ATLAS_EXECUTION_MODELS)\s*=\s*(.*?)\s*', line)
        if match and match[1] not in values:
            value = match[2]
            if len(value) > 1 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            values[match[1]] = value
    return values
