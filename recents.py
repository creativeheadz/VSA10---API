# recents.py — JSON-backed memory of recent IDs and recently-run scripts.
import json
import os
import time

_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.vsa_recents.json')

MAX_IDS_PER_ARG = 8
MAX_SCRIPTS = 8


def _load():
    if not os.path.exists(_PATH):
        return {'ids': {}, 'scripts': []}
    try:
        with open(_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data.setdefault('ids', {})
        data.setdefault('scripts', [])
        return data
    except Exception:
        return {'ids': {}, 'scripts': []}


def _save(data):
    try:
        with open(_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass  # best-effort


# ─── IDs ───────────────────────────────────────────────────────────────────

def get_recent_ids(arg_name):
    """Return list of {id, label, ts} for an arg name, newest first."""
    data = _load()
    return data['ids'].get(arg_name.lower(), [])


def record_id(arg_name, value, label=''):
    """Record a recently-used id for an arg name."""
    if not value:
        return
    data = _load()
    key = arg_name.lower()
    bucket = data['ids'].setdefault(key, [])
    # de-dup
    bucket = [b for b in bucket if b.get('id') != value]
    bucket.insert(0, {'id': value, 'label': label or '', 'ts': int(time.time())})
    data['ids'][key] = bucket[:MAX_IDS_PER_ARG]
    _save(data)


# ─── scripts ───────────────────────────────────────────────────────────────

def get_recent_scripts():
    """Return list of {folder, file, ts}, newest first."""
    return _load()['scripts']


def record_script(folder, file_name):
    """Record that a script was run."""
    data = _load()
    entry = {'folder': folder, 'file': file_name, 'ts': int(time.time())}
    bucket = [s for s in data['scripts'] if not (s.get('folder') == folder and s.get('file') == file_name)]
    bucket.insert(0, entry)
    data['scripts'] = bucket[:MAX_SCRIPTS]
    _save(data)
