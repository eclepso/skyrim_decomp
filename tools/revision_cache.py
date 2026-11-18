"""Local memoization of successful checks on exact content snapshots.

No acceptance evidence is cached here. Changed source, tools, metadata, paths or modes get a
new key; failures are never saved. Publication results bind the immutable index and the current
private denylist; working file contents are always hashed before reuse.
"""
import hashlib
from contextlib import contextmanager
import json
import locale
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile


def directory(root):
    """Lane clones point at a shared private store; ordinary checkouts stay self-contained."""
    setting = subprocess.run(['git', 'config', '--local', '--get', 'skyrim.revisionCacheDirectory'],
                             cwd=root, capture_output=True, text=True)
    return Path(setting.stdout.strip()) if setting.returncode == 0 else Path(root) / '.local/revision-cache'


def tools_digest(root):
    h = hashlib.sha256()
    for path in sorted((Path(root) / 'tools').rglob('*')):
        if path.suffix in ('.py', '.json') and path.is_file() and '__pycache__' not in path.parts:
            h.update(path.relative_to(root).as_posix().encode() + b'\0')
            h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.digest()


# Bind loaded code too: changing a long-lived caller's files cannot relabel its old code as
# a pass from a new tool revision. The current files are independently included below.
TOOLS_AT_IMPORT = tools_digest(Path(__file__).resolve().parents[1])


def runtime_digest():
    # A shared store may be transferred to a different host. Path and default text decoding
    # semantics must agree before reusing a validator/scanner result there.
    return hashlib.sha256(repr((os.name, tuple(sys.version_info), sys.flags.utf8_mode,
                                locale.getencoding(), sys.getfilesystemencoding())).encode()).digest()


def policy_digest(root):
    from check import publication_policy_path
    h = hashlib.sha256()
    for name, variable in (('anonymity.json', 'SR_ANONYMITY_CONFIG'),
                           ('publication-forbidden.json', 'SR_PUBLICATION_FORBIDDEN_CONFIG')):
        path = publication_policy_path(root, name, variable)
        h.update(name.encode() + b'\0')
        h.update(hashlib.sha256(path.read_bytes()).digest() if path.is_file() else b'missing')
    return h.digest()


def snapshot(root, staged=False):
    root = Path(root)
    records = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=root)
    h = hashlib.sha256(b'check-snapshot-v2\0' + records)
    h.update(runtime_digest())
    untracked = []
    if not staged:
        changed = subprocess.check_output(['git', 'diff', '--name-only', '-z'], cwd=root).split(b'\0')
        untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z'], cwd=root).split(b'\0')
        # Include ignored public context too: an ignored header can affect include resolution,
        # and ignored evidence can affect existence checks. Never walk private storage.
        ignored = subprocess.check_output(['git', 'ls-files', '--others', '--ignored', '--exclude-standard', '-z',
                                            '--', 'reconstruction', 'builds', 'data', 'findings', 'reports', 'docs'],
                                           cwd=root).split(b'\0')
        for raw in sorted(set(changed + untracked + ignored) - {b''}):
            path = root / raw.decode()
            h.update(raw + b'\0')
            if path.is_symlink():
                h.update(b'symlink\0' + os.fsencode(os.readlink(path)))
                h.update(str(path.lstat().st_mode).encode())
            elif path.is_file():
                h.update(hashlib.sha256(path.read_bytes()).digest())
                h.update(str(path.stat().st_mode).encode())
            else:
                h.update(b'missing')
    # Staged validation still executes the tools of the current checkout.
    h.update(tools_digest(root))
    h.update(tools_digest(Path(__file__).resolve().parents[1]))
    h.update(TOOLS_AT_IMPORT)
    h.update(policy_digest(root))
    # Lint optionally verifies the notice against the private pinned checkout's licence.
    from lint_reconstruction import LICENCE_FILES, LOCAL_SOURCES
    for name in sorted(LICENCE_FILES.values()):
        path = LOCAL_SOURCES / name
        h.update(name.encode() + b'\0')
        h.update(hashlib.sha256(path.read_bytes()).digest() if path.is_file() else b'missing')
    # The same snapshot has different skeleton semantics before and after staging.
    h.update(b'\0'.join(sorted(filter(None, untracked))))
    return h.hexdigest()


def read(root, namespace, key):
    try:
        return json.loads((directory(root) / namespace / (key + '.json')).read_text())
    except (OSError, ValueError):
        return None


def save(root, namespace, key, value):
    base = directory(root) / namespace
    path = None
    try:
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', dir=base, delete=False) as out:
            path = Path(out.name)
            json.dump(value, out)
        os.replace(path, base / (key + '.json'))
    except OSError:
        pass  # A read-only checkout still runs all checks.
    finally:
        if path is not None:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass


class BlobMemo:
    """Successful publication scans only. SQLite commits atomically merge concurrent writers.

    Read the scanner/policy partition once, rather than open one cache file per public file.
    Uncommitted additions are discarded if any index or working-file scan fails.
    """
    def __init__(self, root, context):
        self.path = directory(root) / 'publication-blobs.sqlite3'
        self.context, self.saved, self.added = context, {}, {}
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.connect() as db:
                db.execute('CREATE TABLE IF NOT EXISTS blobs '
                           '(context TEXT, key TEXT, digest TEXT, PRIMARY KEY (context, key))')
                self.saved = dict(db.execute('SELECT key, digest FROM blobs WHERE context = ?', (context,)))
        except (OSError, sqlite3.Error):
            pass

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        try:
            with db:
                yield db
        finally:
            db.close()

    def key(self, blob, name, mode):
        return hashlib.sha256((blob + '\0' + name + '\0' + mode).encode()).hexdigest()

    def get(self, key):
        digest = self.added.get(key, self.saved.get(key))
        return digest if isinstance(digest, str) and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest) else None

    def put(self, key, digest):
        self.added[key] = digest

    def commit(self):
        if not self.added and os.environ.get('SR_REVISION_CACHE_PRUNE') != '1':
            return
        try:
            with self.connect() as db:
                db.executemany('INSERT OR REPLACE INTO blobs VALUES (?, ?, ?)',
                               ((self.context, key, value) for key, value in self.added.items()))
                if os.environ.get('SR_REVISION_CACHE_PRUNE') == '1':
                    # A store carried between CI runs would otherwise keep one partition per tools
                    # revision forever; only this scanner's partition can be hit again.
                    db.execute('DELETE FROM blobs WHERE context != ?', (self.context,))
        except sqlite3.Error:
            pass  # Cache contention/corruption is a miss, never a validation result.
