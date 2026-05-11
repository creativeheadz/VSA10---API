# output_utils.py — tee stdout, then offer pager / save-to-file / JSON field filter.
import io
import json
import os
import re
import sys
import time

PAGE_LINES = 30
LONG_THRESHOLD = 40  # lines beyond which we offer pager


class _Tee(io.TextIOBase):
    """Write to multiple streams. Used so the user sees output live AND we capture it."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            try:
                st.write(s)
            except Exception:
                pass
        return len(s)

    def flush(self):
        for st in self.streams:
            try:
                st.flush()
            except Exception:
                pass

    def isatty(self):
        for st in self.streams:
            try:
                if st.isatty():
                    return True
            except Exception:
                pass
        return False


class capture_stdout:
    """Context manager that tees stdout to the user AND a buffer."""

    def __init__(self):
        self.buffer = io.StringIO()
        self._saved = None

    def __enter__(self):
        self._saved = sys.stdout
        sys.stdout = _Tee(self._saved, self.buffer)
        return self

    def __exit__(self, *exc):
        sys.stdout = self._saved

    @property
    def text(self):
        return self.buffer.getvalue()


# ─── post-run actions ──────────────────────────────────────────────────────

_JSON_RE = re.compile(r'(\{[\s\S]*\}|\[[\s\S]*\])')


def _extract_json(text):
    """Find the largest JSON block in text and return the parsed object, or None."""
    matches = list(_JSON_RE.finditer(text))
    if not matches:
        return None
    # Try matches biggest-first.
    matches.sort(key=lambda m: len(m.group(0)), reverse=True)
    for m in matches:
        try:
            return json.loads(m.group(0))
        except Exception:
            continue
    return None


def _pager(text):
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        chunk = lines[i:i + PAGE_LINES]
        print('\n'.join(chunk))
        i += PAGE_LINES
        if i < len(lines):
            ans = input(f"-- more ({i}/{len(lines)}) -- [enter=next, q=quit] ").strip().lower()
            if ans == 'q':
                return


def _save(text):
    ts = time.strftime('%Y%m%d-%H%M%S')
    default = f"vsa_output_{ts}.txt"
    name = input(f"Save as [{default}]: ").strip() or default
    path = name if os.path.isabs(name) else os.path.join(os.getcwd(), name)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"  saved → {path}")
    except Exception as e:
        print(f"  save failed: {e}")


def _dotpath_lookup(obj, path):
    """Walk a dot-path like 'Data.0.Name' or 'Data.*.Id' through obj."""
    parts = [p for p in path.split('.') if p != '']
    cur = [obj]
    for p in parts:
        nxt = []
        for c in cur:
            if p == '*':
                if isinstance(c, list):
                    nxt.extend(c)
                elif isinstance(c, dict):
                    nxt.extend(c.values())
            elif p.isdigit() and isinstance(c, list):
                idx = int(p)
                if 0 <= idx < len(c):
                    nxt.append(c[idx])
            elif isinstance(c, dict) and p in c:
                nxt.append(c[p])
        cur = nxt
        if not cur:
            return []
    return cur


def _json_filter(parsed):
    print("\n  Dot-path examples: Data.0.Name   Data.*.Id   value.*.DisplayName")
    while True:
        path = input("  field path (blank to stop): ").strip()
        if not path:
            return
        try:
            results = _dotpath_lookup(parsed, path)
        except Exception as e:
            print(f"  path error: {e}")
            continue
        if not results:
            print("  (no matches)")
            continue
        if len(results) == 1:
            print(json.dumps(results[0], indent=2))
        else:
            print(json.dumps(results, indent=2))


def offer_post_actions(text):
    """Called after a script finishes. If output is large or JSON, offer follow-ups."""
    line_count = text.count('\n')
    parsed = _extract_json(text)
    if line_count < LONG_THRESHOLD and parsed is None:
        return

    opts = []
    if line_count >= LONG_THRESHOLD:
        opts.append('[p] page')
    opts.append('[s] save')
    if parsed is not None:
        opts.append('[j] JSON field filter')
    opts.append('[enter] continue')
    print('\n  Post-run: ' + '   '.join(opts))

    while True:
        choice = input('  > ').strip().lower()
        if not choice:
            return
        if choice == 'p':
            _pager(text)
        elif choice == 's':
            _save(text)
        elif choice == 'j' and parsed is not None:
            _json_filter(parsed)
        else:
            return
