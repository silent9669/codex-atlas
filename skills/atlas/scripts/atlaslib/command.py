"""Parse the Atlas chat command without shell evaluation."""
import shlex


def parse(message):
    tokens = shlex.split(message)
    if not tokens or tokens.pop(0) != '/codex-atlas':
        raise ValueError('Use /codex-atlas followed by a task.')
    options = {'run': False, 'allow_edits': False, 'model': None}
    parts = []
    for token in tokens:
        key, separator, value = token.partition('=')
        if separator and key in {'TASK', 'MODEL', 'RUN', 'ALLOW_EDITS'}:
            if key == 'TASK': parts.append(value)
            elif key == 'MODEL': options['model'] = None if value == 'auto' else value
            else:
                if value.lower() not in {'true','false'}: raise ValueError(key + ' must be true or false.')
                options['run' if key == 'RUN' else 'allow_edits'] = value.lower() == 'true'
        else: parts.append(token)
    task = ' '.join(parts).strip()
    if not task: raise ValueError('Add a task after /codex-atlas.')
    if options['allow_edits'] and not options['run']:
        raise ValueError('ALLOW_EDITS=true requires RUN=true.')
    return task, options
