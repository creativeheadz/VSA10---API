# safety.py — destructive-action confirmation, dry-run, and prettier slumber errors.
import slumber

DESTRUCTIVE_PREFIXES = ('delete_', 'cancel_', 'remove_', 'destroy_')


# ─── destructive-action confirmation ───────────────────────────────────────

def is_destructive(file_name):
    """Heuristic: filename prefix matches a destructive verb."""
    stem = file_name.lower()
    return any(stem.startswith(p) for p in DESTRUCTIVE_PREFIXES)


def confirm_destructive(file_name):
    """Block until the user types YES (case-sensitive). Return True if confirmed."""
    print(f"\n  ⚠  '{file_name}' looks destructive.")
    answer = input("  Type YES to proceed, anything else to abort: ")
    return answer == 'YES'


# ─── dry-run ───────────────────────────────────────────────────────────────

_DRY_RUN_STATE = {'active': False, 'orig_request': None}


def _dry_request(self, method, data=None, files=None, params=None):
    if method.upper() == 'GET':
        return _DRY_RUN_STATE['orig_request'](self, method, data=data, files=files, params=params)
    # Show what would have been sent.
    try:
        target = self.url()
    except Exception:
        target = '?'
    print(f"\n  [DRY-RUN] {method.upper()} {target}")
    if params:
        print(f"           params={params}")
    if data is not None:
        print(f"           body={data}")
    return {'_dry_run': True, 'method': method, 'url': target, 'body': data}


def set_dry_run(active):
    if active and not _DRY_RUN_STATE['active']:
        _DRY_RUN_STATE['orig_request'] = slumber.Resource._request
        slumber.Resource._request = _dry_request
        _DRY_RUN_STATE['active'] = True
    elif not active and _DRY_RUN_STATE['active']:
        slumber.Resource._request = _DRY_RUN_STATE['orig_request']
        _DRY_RUN_STATE['active'] = False


def is_dry_run():
    return _DRY_RUN_STATE['active']


# ─── prettier slumber errors ───────────────────────────────────────────────

_ERROR_PATCH_APPLIED = False


def install_error_formatter():
    """Patch slumber's HttpClientError so str(e) includes response body."""
    global _ERROR_PATCH_APPLIED
    if _ERROR_PATCH_APPLIED:
        return
    try:
        from slumber import exceptions as sx
    except Exception:
        return

    targets = []
    for name in ('SlumberHttpBaseException', 'HttpClientError', 'HttpServerError', 'HttpNotFoundError'):
        cls = getattr(sx, name, None)
        if cls:
            targets.append(cls)

    def __str__(self):
        parts = []
        resp = getattr(self, 'response', None)
        if resp is not None:
            status = getattr(resp, 'status_code', None)
            if status is not None:
                parts.append(f"HTTP {status}")
            url = getattr(resp, 'url', None)
            if url:
                parts.append(url)
        content = getattr(self, 'content', None)
        if content:
            if isinstance(content, bytes):
                try:
                    content = content.decode('utf-8', errors='replace')
                except Exception:
                    content = str(content)
            snippet = content if len(content) < 800 else content[:800] + ' …(truncated)'
            parts.append(snippet)
        if not parts:
            return self.__class__.__name__
        return ' | '.join(parts)

    for cls in targets:
        cls.__str__ = __str__
    _ERROR_PATCH_APPLIED = True
