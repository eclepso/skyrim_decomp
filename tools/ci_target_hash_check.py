#!/usr/bin/env python3
"""Advisory PR compilation using trusted base tools and target-hash commitments only.

Never run PR tools or resulting objects. Compiler output remains in scratch. No image input,
acceptance record, network credential, artifact upload or cache is part of this check.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import ci_hash_check as public
import contrib
import lint_reconstruction as lint
from pecoff import Reject
from source_digest import include_closure, tu_digest
import target_hashes as hashes

DEFAULT_RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'
# Optional source-header request for a new unit with no accepted symbol binding yet. It is a
# claim about which public target to try, never evidence of identity or acceptance.
REQUEST = re.compile(r'^// CI hash: (0x[0-9a-fA-F]+) (\S+)\s*$', re.M)
SHA = re.compile(r'[0-9a-f]{40}')
CI_INPUTS = ('data/target-hashes/', 'tools/toolchain/', 'tools/ci_',
             'tools/target_hashes.py', 'tools/contrib.py', 'tools/contributor_standing.py',
             'tools/build_leaderboard.py', 'tools/build_model_trend.py', '.gitattributes',
             '.github/workflows/ci-target-hash.yml')


def git(root, *args):
    return subprocess.run(['git', *args], cwd=root, capture_output=True, check=True).stdout


def trusted_inputs(root):
    manifest = hashes.load_manifest(root)
    return dict(manifest_sha256=hashes.digest((root / hashes.MANIFEST).read_bytes()),
                normalizer_sha256=manifest['normalizer_sha256'],
                comparator_sha256=manifest['comparator_sha256'],
                compiler_pins_sha256=hashes.digest((root / 'tools/verifier/pinned.sha256').read_bytes()))


def prepare(root, base, head, work):
    if not SHA.fullmatch(base) or not SHA.fullmatch(head):
        raise ValueError('revision must be a full SHA')
    if git(root, 'rev-parse', 'HEAD').decode().strip() != base:
        raise ValueError('tools must be from the trusted base revision')
    merge_base = git(root, 'merge-base', base, head).decode().strip()
    diff = git(root, 'diff', '--no-renames', '--name-status', '-z', merge_base, head).split(b'\0')
    rows = []
    for i in range(0, len(diff) - 1, 2):
        status, name = diff[i].decode('ascii'), diff[i + 1].decode('utf-8')
        if not contrib.UNIT_PATH.fullmatch(name):
            if name.startswith(CI_INPUTS):
                continue  # Never read or execute PR tooling; test trusted base references instead.
            raise ValueError('outside contributor intake scope')
        if status not in ('A', 'M'):
            raise ValueError('outside contributor intake scope')
        # Read only bounded, regular source blobs. Never follow a PR symlink or check out head.
        meta = git(root, 'ls-tree', head, '--', name).decode().split()
        if len(meta) < 3 or meta[0] != '100644' or meta[1] != 'blob':
            raise ValueError('source is not a regular file')
        size = int(git(root, 'cat-file', '-s', meta[2]))
        if size > contrib.MAX_UNIT_FILE_BYTES:
            raise ValueError('source exceeds contributor file cap')
        blob = git(root, 'cat-file', 'blob', meta[2])
        if b'\0' in blob:
            raise ValueError('source is not text')
        blob.decode('utf-8-sig')
        rows.append((name, blob))
    if not rows:
        return root, []
    tree = work / 'source'
    tree.mkdir(parents=True)
    for name in ('reconstruction', 'builds', 'findings', 'reports'):
        shutil.copytree(root / name, tree / name, symlinks=False)
    target = json.loads((root / 'builds/target.json').read_text())['build_id']
    for name, blob in rows:
        path = tree / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
    for name, _blob in rows:
        if lint.lint_file(tree, name, target):
            raise ValueError('contributor source lint failed')
    return tree, [name for name, _ in rows]


def bindings(root):
    """Only public main records provide existing symbol/recipe bindings."""
    inventory = json.loads((root / 'data/progress.json').read_text())
    result = {}
    for fn in inventory['functions']:
        if not fn.get('report') or not (root / fn['report']).is_file():
            continue
        record = json.loads((root / fn['report']).read_text())
        if not record.get('source', {}).get('compiled') or not record.get('runs'):
            continue
        report = record['runs'][0]['report']
        # Contract v3 internal selectors require more than a bare symbol; report no-target.
        if report.get('contract_version') != 2:
            continue
        result.setdefault(record['source']['compiled'], []).append(
            dict(rva=fn['rva'], symbol=report['function']['symbol'], recipe=record['recipe']['path']))
    return result


def requests(tree, changed, known):
    from check_source_digest import include_closure as cached_closure, source_digest_cache
    import revision_cache
    tree = Path(tree)
    key = None
    # Scratch CI trees have no git metadata; scoped resolution still avoids repeated directory scans.
    if (tree / '.git').exists():
        key = revision_cache.snapshot(tree)
    index = revision_cache.read(tree, 'include-index', key) if key else None
    if index is None:
        index = {}
        with source_digest_cache():
            for path in sorted((tree / 'reconstruction').rglob('*.cpp')):
                unit = path.relative_to(tree).as_posix()
                for name in cached_closure(tree, unit):
                    index.setdefault(name, []).append(unit)
        if key and revision_cache.snapshot(tree) == key:
            revision_cache.save(tree, 'include-index', key, index)
    units = {name for name in changed if name.endswith('.cpp')}
    for name in changed:
        units.update(index.get(name, []))
    result = []
    for unit in sorted(units):
        entries = {r['rva']: dict(r) for r in known.get(unit, [])}
        # New source may request an RVA/symbol, but cannot select the target mask, size or recipe.
        for rva, symbol in REQUEST.findall((tree / unit).read_text(encoding='utf-8-sig')[:8192]):
            value = int(rva, 16)
            if value not in entries:
                entries[value] = dict(rva=value, symbol=symbol, recipe=DEFAULT_RECIPE)
        if not entries:
            result.append(dict(unit=unit, rva=None, symbol=None, recipe=DEFAULT_RECIPE))
        else:
            result += [dict(unit=unit, **r) for r in entries.values()]
    return result


def compile_requests(root, tree, requests_, bindir, work, manifest):
    ctx = contrib.Ctx(repo=root, platform='win32', interactive=False)
    tool = dict(status='ok', flavour='native', bin=str(bindir), root=str(bindir.parents[6]))
    targets = {row['rva']: row for row in manifest['functions']}
    built = {}
    rows = []
    for ref in requests_:
        target = targets.get(ref['rva'])
        row = dict(rva=hex(ref['rva']) if ref['rva'] is not None else None, unit=ref['unit'],
                   result='no-target')
        if ref['recipe'] not in manifest['recipe_sha256']:
            rows.append(row)
            continue
        key = ref['unit'], ref['recipe']
        if key not in built:
            try:
                recipe = json.loads((root / ref['recipe']).read_text())
                _, includes = contrib.sdk_include_dirs(ctx, tool['root'], recipe['sdk'])
                if not includes or includes[0].parent.name != recipe['sdk']:
                    raise ValueError('pinned SDK missing')
                built[key] = contrib.compile_unit(ctx, tree, ref['unit'], ref['recipe'],
                                                work / str(len(built)), tool)['object'].read_bytes()
            except (ValueError, OSError, Reject, contrib.Stop, subprocess.TimeoutExpired):
                built[key] = None
        if built[key] is None:
            row['result'], row['reason'] = 'mismatch', 'compile-failed'
        elif target is None or ref['symbol'] is None or target['extraction'] == 'unmasked-unsupported':
            row['reason'] = 'published-target-or-binding-unavailable'
        else:
            try:
                row['result'] = hashes.candidate(built[key], ref['symbol'], target)
                row['source_sha256'] = tu_digest(tree, include_closure(tree, ref['unit']))
                row['recipe_sha256'] = hashes.digest((root / ref['recipe']).read_bytes())
            except (ValueError, Reject):
                row['result'], row['reason'] = 'no-target', 'unsupported-object-layout'
        rows.append(row)
    return rows


def sample(root, bindir, work, manifest):
    rvas = json.loads((root / 'data/target-hashes/determinism-sample.json').read_text())['rvas']
    refs = [dict(public.reference(root, rva), rva=rva) for rva in rvas]
    requests_ = [dict(unit=r['unit'], rva=r['rva'], symbol=r['symbol'], recipe=r['recipe']) for r in refs]
    first = compile_requests(root, root, requests_, bindir, work / 'first', manifest)
    second = compile_requests(root, root, requests_, bindir, work / 'second', manifest)
    return [dict(row, deterministic=row['result'] == other['result'] == 'hash-match')
            for row, other in zip(first, second)]


def classify(head_rows, base_rows):
    """Label each head row against the same unit/RVA compiled from the base tree.

    Only `regressed` (hash-match at base, no match at head) may block; debt that already failed
    at base and functions that are new in the PR are reported, not enforced.
    """
    base = {(r['unit'], r['rva']): r['result'] for r in base_rows}
    rows = []
    for row in head_rows:
        before = base.get((row['unit'], row['rva']))
        if row['result'] == 'hash-match':
            status = 'pass'
        elif row['result'] == 'no-target':
            status = 'unverified'
        elif before == 'hash-match':
            status = 'regressed'
        elif before == 'mismatch':
            status = 'preexisting-fail'
        else:
            status = 'fail'
        rows.append(dict(row, status=status, base=before))
    return rows


def regress(root, tree, refs, bindir, work, manifest):
    head = compile_requests(root, tree, refs, bindir, work / 'head', manifest)
    # Units absent from the base tree are new; compiling them there would only add noise.
    old = [r for r in refs if (root / r['unit']).is_file()]
    base = compile_requests(root, root, old, bindir, work / 'base', manifest) if old else []
    return classify(head, base)


def summary_text(report):
    lines = ['Advisory target hash results; acceptance not evaluated. The current acceptance rule',
             'still requires its independent hosts and Reviewer. Hash equality omits reference identity.',
             '', '| Function RVA | Unit | Result |', '| --- | --- | --- |']
    for row in report.get('functions', []):
        result = {'hash-match': 'PASS (hash only)', 'mismatch': 'FAIL', 'no-target': 'UNVERIFIED'}.get(row['result'], 'ERROR')
        if row.get('status'):
            result = row['status'].upper()
        lines.append(f'| {row["rva"] or "unbound"} | {row["unit"]} | {result} |')
    if report.get('error'):
        lines += ['', 'Check could not complete: ' + report['error'] + '. No strike.']
    return '\n'.join(lines) + '\n'


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('prepare', 'check', 'regress', 'sample'))
    p.add_argument('--base')
    p.add_argument('--head')
    p.add_argument('--bin', type=Path)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--map-out', type=Path, help='regress: write {rva-or-unit: status} for the PR bot')
    a = p.parse_args(argv)
    report = dict(schema=1, kind='target-hash-check', head_sha=a.head,
                  base_sha=a.base, normalization_version=hashes.VERSION, acceptance='not-evaluated')
    try:
        a.work.mkdir(parents=True, exist_ok=True)
        report.update(trusted_inputs(ROOT))
        manifest = hashes.load_manifest(ROOT)
        if a.command == 'prepare':
            tree, changed = prepare(ROOT, a.base, a.head, a.work)
            refs = requests(tree, changed, bindings(ROOT))
            (a.work / 'requests.json').write_text(json.dumps(refs))
            report['intake'] = 'pass'
            report['requested_functions'] = len(refs)
            if os.environ.get('GITHUB_OUTPUT'):
                with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
                    out.write('mode=' + ('check' if changed else 'sample') + '\n')
        else:
            if not a.bin or public.probe(ROOT, a.bin)['toolset'] != 'MATCH':
                raise ValueError('compiler pin mismatch')
            report['toolset'] = 'MATCH'
            if a.command == 'sample':
                report['functions'] = sample(ROOT, a.bin, a.work, manifest)
            elif a.command == 'regress':
                refs = json.loads((a.work / 'requests.json').read_text())
                report['functions'] = regress(ROOT, a.work / 'source', refs, a.bin, a.work / 'objects', manifest)
                if a.map_out:
                    a.map_out.parent.mkdir(parents=True, exist_ok=True)
                    a.map_out.write_text(json.dumps({r['rva'] or r['unit']: r['status'] for r in report['functions']},
                                                    indent=2, sort_keys=True) + '\n')
            else:
                refs = json.loads((a.work / 'requests.json').read_text())
                report['functions'] = compile_requests(ROOT, a.work / 'source', refs, a.bin,
                                                       a.work / 'objects', manifest)
    except (ValueError, OSError, KeyError, StopIteration, Reject, contrib.Stop,
            subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        report['error'] = type(exc).__name__
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
            summary.write(summary_text(report))
    if a.command == 'regress':
        return int('error' in report or any(r['status'] == 'regressed' for r in report.get('functions', [])))
    return int('error' in report or any(r['result'] == 'mismatch' for r in report.get('functions', []))
               or (a.command == 'sample' and any(not r['deterministic'] for r in report['functions'])))


if __name__ == '__main__':
    sys.exit(main())
