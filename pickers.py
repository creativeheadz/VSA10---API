# pickers.py — interactive entity selectors for VSA arg prompts.
import slumber
import config

PAGE_SIZE = 20

_ID_KEYS = ('Id', 'AgentId', 'DeviceId', 'OrganizationId', 'OrgId', 'SiteId', 'GroupId')
_NAME_KEYS = ('DisplayName', 'Name', 'ComputerName', 'Hostname', 'AgentName',
              'OrganizationName', 'OrgName', 'SiteName', 'GroupName')
_ONLINE_KEYS = ('Online', 'IsOnline', 'AgentOnline', 'Connected')
_STATUS_KEYS = ('Status', 'AgentStatus', 'ConnectionStatus')


def _api():
    return slumber.API(config.ENDPOINT, auth=(config.TOKEN_ID, config.TOKEN_SECRET))


def _unwrap(result):
    """VSA responses may be a bare list, {'Data': [...]}, or {'value': [...]}."""
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        for key in ('Data', 'value', 'Items', 'Results'):
            if key in result and isinstance(result[key], list):
                return result[key]
    return []


def _pick_id(item):
    for k in _ID_KEYS:
        if k in item and item[k] not in (None, ''):
            return str(item[k])
    return None


def _pick_name(item):
    for k in _NAME_KEYS:
        if k in item and item[k]:
            return str(item[k])
    return ''


def _is_online(item):
    for k in _ONLINE_KEYS:
        if k in item:
            v = item[k]
            if isinstance(v, bool):
                return v
            if isinstance(v, str):
                return v.lower() in ('true', 'online', 'up', 'connected', 'yes')
    for k in _STATUS_KEYS:
        if k in item and isinstance(item[k], str):
            return item[k].lower() in ('online', 'up', 'connected')
    return None  # unknown


def _fetch(endpoint_attr, top, skip):
    """Fetch a page from /<endpoint_attr>. Tries $top/$skip then top/skip."""
    api = _api()
    resource = getattr(api, endpoint_attr)
    for params in ({'$top': str(top), '$skip': str(skip)},
                   {'top': str(top), 'skip': str(skip)}):
        try:
            return _unwrap(resource.get(**params))
        except Exception:
            continue
    # Last-ditch: no params.
    return _unwrap(resource.get())


def _normalize(items):
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        ident = _pick_id(it)
        if not ident:
            continue
        out.append({
            'id': ident,
            'label': _pick_name(it) or ident,
            'online': _is_online(it),
            'raw': it,
        })
    return out


# ─── per-entity loaders ────────────────────────────────────────────────────

def fetch_devices(top=PAGE_SIZE, skip=0):
    return _normalize(_fetch('devices', top, skip))


def fetch_organizations(top=PAGE_SIZE, skip=0):
    # American spelling per the API (see Organisations/get_all_organisations.py).
    return _normalize(_fetch('organizations', top, skip))


def fetch_sites(top=PAGE_SIZE, skip=0):
    return _normalize(_fetch('sites', top, skip))


def fetch_groups(top=PAGE_SIZE, skip=0):
    return _normalize(_fetch('groups', top, skip))


# ─── registry ──────────────────────────────────────────────────────────────

PICKERS = {
    'device': {'fetch': fetch_devices, 'label': 'device', 'supports_online_filter': True},
    'agent': {'fetch': fetch_devices, 'label': 'device', 'supports_online_filter': True},
    'endpoint': {'fetch': fetch_devices, 'label': 'device', 'supports_online_filter': True},
    'organization': {'fetch': fetch_organizations, 'label': 'organization', 'supports_online_filter': False},
    'organisation': {'fetch': fetch_organizations, 'label': 'organization', 'supports_online_filter': False},
    'org': {'fetch': fetch_organizations, 'label': 'organization', 'supports_online_filter': False},
    'site': {'fetch': fetch_sites, 'label': 'site', 'supports_online_filter': False},
    'group': {'fetch': fetch_groups, 'label': 'group', 'supports_online_filter': False},
}


def resolve_picker(arg_name):
    """Return picker config for an arg name like 'device_id', or None."""
    lower = arg_name.lower()
    for key, cfg in PICKERS.items():
        if key in lower:
            return cfg
    return None


# ─── interactive picker ────────────────────────────────────────────────────

def pick(arg_name, online_default=True):
    """Run an interactive picker for arg_name. Returns the chosen id string or None."""
    cfg = resolve_picker(arg_name)
    if not cfg:
        return None

    label = cfg['label']
    fetch = cfg['fetch']
    online_filter = cfg['supports_online_filter'] and online_default
    substr = ''
    skip = 0

    cache = []  # cumulative results so far

    while True:
        # Fetch more if we haven't seen this page yet.
        needed = skip + PAGE_SIZE
        while len(cache) < needed:
            try:
                page = fetch(top=PAGE_SIZE, skip=len(cache))
            except Exception as e:
                print(f"  ! failed to fetch {label}s: {e}")
                return None
            if not page:
                break
            cache.extend(page)
            if len(page) < PAGE_SIZE:
                break  # end of data

        # Apply filters.
        filtered = cache
        if online_filter:
            # If "online" field is unknown across the board, don't strip everything.
            with_known = [d for d in filtered if d['online'] is not None]
            if with_known:
                filtered = [d for d in filtered if d['online'] is True]
        if substr:
            s = substr.lower()
            filtered = [d for d in filtered if s in d['label'].lower() or s in d['id'].lower()]

        page_items = filtered[skip:skip + PAGE_SIZE]

        print()
        flag = []
        if cfg['supports_online_filter']:
            flag.append('online only' if online_filter else 'all')
        if substr:
            flag.append(f"filter: '{substr}'")
        suffix = f"  [{' | '.join(flag)}]" if flag else ''
        print(f"--- Pick a {label}{suffix} ---")

        if not page_items:
            print("  (no matches)")
        else:
            for i, item in enumerate(page_items, 1):
                online_mark = ''
                if item['online'] is True:
                    online_mark = ' ●'  # ●
                elif item['online'] is False:
                    online_mark = ' ○'  # ○
                print(f"  [{i:2d}] {item['label']}{online_mark}   ({item['id']})")

        options = ['[n]ext', '[p]rev', '[f]ilter', '[c]lear filter']
        if cfg['supports_online_filter']:
            options.append('[o]nline toggle')
        options.append('[m]anual entry')
        options.append('[q]uit picker')
        print('  ' + '   '.join(options))

        choice = input(f"Choose {label} or option: ").strip().lower()

        if not choice:
            continue
        if choice == 'q':
            return None
        if choice == 'm':
            v = input(f"Enter {arg_name} manually: ").strip()
            return v or None
        if choice == 'n':
            if len(filtered) > skip + PAGE_SIZE:
                skip += PAGE_SIZE
            else:
                print("  (no more pages)")
            continue
        if choice == 'p':
            skip = max(0, skip - PAGE_SIZE)
            continue
        if choice == 'f':
            substr = input("Substring filter (blank to clear): ").strip()
            skip = 0
            continue
        if choice == 'c':
            substr = ''
            skip = 0
            continue
        if choice == 'o' and cfg['supports_online_filter']:
            online_filter = not online_filter
            skip = 0
            continue
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(page_items):
                return page_items[idx - 1]['id']
            print("  (invalid number)")
            continue
        print("  (unrecognized option)")
