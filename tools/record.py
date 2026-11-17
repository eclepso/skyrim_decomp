#!/usr/bin/env python3
"""Record newly matched functions on main right after the bot merged their source.

    python3 tools/record.py --build ID --rva 0x1000 [--rva ...] --review review.json \
        --author LOGIN [--records DIR] [--root TREE] [--push]

For each function it writes the sanitized Reviewer record next to the function's own match
record, flips that one inventory row to `matched` pointing at its own report, and patches that
one line of reconstruction/INDEX.md. Nothing else in the inventory is touched or regenerated:
the cost of one acceptance stays proportional to the functions it names.

A function is recorded only if the validator accepts the result; anything it refuses is left
as it was and reported. `--push` commits and pushes to main, and on a non-fast-forward fetches,
rebases and tries again, re-applying from the new main when the rebase conflicts.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_index  # noqa: E402
from check import _json_or_none  # noqa: E402
from check import (ROOT, DIGEST_METHOD, REVIEW_RECORD_SCHEMA, record_code_section,  # noqa: E402
                   review_record_path, validate_match, validate_review)

PROGRESS = 'data/progress.json'
TARGET = 'builds/target.json'
PUSH_ATTEMPTS = 6


def _load(root, name):
    return json.loads((Path(root) / name).read_text())


def review_blob_digest(blob):
    return hashlib.sha256(blob).hexdigest()


def review_record(fn, record, model, task_id, blob, when):
    """The same fields tools/accept_function.py writes for a full, naming-clean approval."""
    return {
        'review_record_schema': REVIEW_RECORD_SCHEMA,
        'function_id': fn['id'], 'build_id': fn['build_id'], 'rva': fn['rva'], 'size': fn['size'],
        'source_digest_method': DIGEST_METHOD, 'source_digest': record['source']['digest'],
        'reviewer_model': model, 'review_task_id': task_id,
        'verdict': 'approve', 'escalation_category': 'none',
        'review_sha256': review_blob_digest(blob), 'review_date': when.date().isoformat(),
        'review_kind': 'full',
        'previous_source_digest': None, 'previous_review_sha256': None,
        'previous_code_section_sha256': None,
        'code_section_sha256': record_code_section(record),
        'naming_findings': [],
    }


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def _patch_index(root, fns):
    """Replace only the changed functions' lines; the table is sorted and one line per function."""
    path = Path(root) / build_index.INDEX
    if not path.is_file():
        return False
    lines = path.read_text().splitlines(keepends=True)
    for fn in fns:
        key = f'| `{fn["build_id"]}` / `0x{fn["rva"]:x}` / {fn["size"]} |'
        hits = [i for i, line in enumerate(lines) if key in line]
        if len(hits) != 1:
            raise ValueError(f'INDEX.md has {len(hits)} lines for {fn["id"]}')
        lines[hits[0]] = build_index.row(fn, Path(root))
    path.write_text(''.join(lines))
    return True


def apply(root, build_id, rvas, review_blob, *, model, task_id, author=None, records=None, when=None):
    """Record what the validator accepts. Returns {'recorded': [rva], 'refused': {rva: reason}, 'files': [...]}."""
    root = Path(root)
    when = when or datetime.now(timezone.utc).replace(microsecond=0)
    data = _load(root, PROGRESS)
    target = _load(root, TARGET)
    by_rva = {fn['rva']: (i, fn) for i, fn in enumerate(data['functions']) if fn['build_id'] == build_id}
    out = {'recorded': [], 'refused': {}, 'files': []}
    changed = []
    for rva in sorted(set(rvas)):
        if rva not in by_rva:
            out['refused'][rva] = 'not in inventory'
            continue
        index, fn = by_rva[rva]
        report = f'reports/{build_id}/0x{rva:x}.json'
        review_path = root / review_record_path(fn)
        written, prior = [], {}
        try:
            source = Path(records) / build_id / f'0x{rva:x}.json' if records is not None else root / report
            if not source.is_file():
                raise ValueError('no match record was produced')
            record = json.loads(source.read_text())
            if author:
                from build_leaderboard import handle
                if not handle(author):
                    raise ValueError('author has no valid public handle')
                record['submitter'] = handle(author)
            # A stacked PR re-confirms functions of a unit that grew; only the identical source is a repeat.
            previous = _json_or_none(review_path) if fn['status'] == 'matched' else None
            if previous and previous.get('source_digest') == record['source']['digest']:
                raise ValueError('already matched')
            if records is not None or author:
                prior[root / report] = (root / report).read_bytes() if (root / report).is_file() else None
                _write_json(root / report, record)
                written.append(root / report)
            candidate = dict(copy.deepcopy(fn), status='matched', report=report, evidence=report)
            record = validate_match(candidate, target, root)
            prior[review_path] = review_path.read_bytes() if review_path.is_file() else None
            _write_json(review_path, review_record(candidate, record, model, task_id, review_blob, when))
            written.append(review_path)
            validate_review(candidate, record, root)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            for path in written:
                if prior.get(path) is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(prior[path])
            out['refused'][rva] = str(exc).splitlines()[0][:200] if str(exc) else type(exc).__name__
            continue
        data['functions'][index] = candidate
        changed.append(candidate)
        out['recorded'].append(rva)
        out['files'] += [report, review_record_path(fn)]
    if changed:
        data['updated_at'] = when.strftime('%Y-%m-%dT%H:%M:%SZ')
        (root / PROGRESS).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
        if _patch_index(root, changed):
            out['files'].append(build_index.INDEX)
        out['files'].append(PROGRESS)
    return out


def git(root, *args, check=True):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, check=check)


def record_and_push(root, build_id, rvas, review_blob, message, push=True, **kwargs):
    """Apply, commit and push; each retry after a lost race starts from the fetched main."""
    last = None
    for attempt in range(PUSH_ATTEMPTS):
        if attempt:
            git(root, 'fetch', '-q', 'origin', 'main')
            rebased = git(root, 'rebase', 'origin/main', check=False)
            if rebased.returncode:
                git(root, 'rebase', '--abort', check=False)
                git(root, 'reset', '-q', '--hard', 'origin/main')
                last = apply(root, build_id, rvas, review_blob, **kwargs)
                if not last['recorded']:
                    return last
                git(root, 'add', '--', *last['files'])
                git(root, 'commit', '-q', '-m', message)
        else:
            last = apply(root, build_id, rvas, review_blob, **kwargs)
            if not last['recorded']:
                return last
            git(root, 'add', '--', *last['files'])
            git(root, 'commit', '-q', '-m', message)
        if not push:
            return last
        pushed = git(root, 'push', '-q', 'origin', 'HEAD:main', check=False)
        if pushed.returncode == 0:
            last['pushed'] = True
            return last
    raise RuntimeError('push to main kept losing the race')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--build', required=True)
    p.add_argument('--rva', action='append', required=True, type=lambda s: int(s, 0))
    p.add_argument('--review', required=True, type=Path, help='the saved review, hashed into the record')
    p.add_argument('--model', default='gpt-6.1-terra')
    p.add_argument('--task-id', required=True)
    p.add_argument('--author')
    p.add_argument('--records', type=Path)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--message')
    p.add_argument('--push', action='store_true')
    a = p.parse_args(argv)
    kwargs = dict(model=a.model, task_id=a.task_id, author=a.author, records=a.records)
    blob = a.review.read_bytes()
    if a.push:
        message = a.message or ('Record ' + ', '.join(f'0x{r:x}' for r in a.rva) +
                                '\n\nCo-Authored-By: Claude <noreply@anthropic.com>')
        result = record_and_push(a.root, a.build, a.rva, blob, message, **kwargs)
    else:
        result = apply(a.root, a.build, a.rva, blob, **kwargs)
    print(json.dumps({'recorded': [f'0x{r:x}' for r in result['recorded']],
                      'refused': {f'0x{r:x}': why for r, why in result['refused'].items()}}))
    return 0 if result['recorded'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
