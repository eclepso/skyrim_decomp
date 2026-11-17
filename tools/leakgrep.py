"""Deterministic grep over a PR's added lines. Prints rule codes and line numbers, never the text.

Not a model and not overridable by one: a model can be talked out of a hit, a regex cannot.
Over-refusal is the intent; the maintainer-only `leakgrep-override` label is the escape hatch.
"""
import argparse
import posixpath
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_LIST = ROOT / '.local/leakgrep-private.txt'
# Pinned compiler headers; anything else quoted must be a repo-relative reconstruction header.
STANDARD_HEADERS = frozenset(('cstddef', 'cstdint', 'cstring', 'climits', 'cfloat', 'cmath', 'type_traits',
                              'utility', 'new', 'limits', 'memory', 'typeinfo', 'atomic', 'algorithm', 'stddef.h', 'stdint.h',
                              'intrin.h'))
MNEMONICS = ('mov movzx movsx movaps movups movss movsd lea push pop call jmp je jne jz jnz ja jae jb jbe jg jge '
             'jl jle cmp test xor and or add sub adc sbb imul mul idiv div inc dec shl shr sar sal rol ror neg not '
             'fld fstp fild fistp fadd fmul fsub fdiv fxch xchg cmov\\w+ set\\w+ rep\\s+movs\\w ret retn').split()
OPERAND = (r'(?:(?:byte|word|dword|qword)\s+ptr\b|\[|[re]?[abcd]x\b|e?[sd]i\b|e?[sb]p\b|[abcd][lh]\b|r\d{1,2}[dwb]?\b'
           r'|xmm\d+|st\(\d\)|0x[0-9a-f]+\s*(?:,|$)|[0-9][0-9a-f]*h\b)')
RULES = (
    ('asm-mnemonic', re.compile(r'^\s*(?://|;|\*|#)?\s*(?:(?:0x)?[0-9a-f]{6,16}:?\s+)?(?:' + '|'.join(MNEMONICS)
                                + r')\s+' + OPERAND, re.I)),
    ('decompiler-ident', re.compile(r'\b(?:FUN|DAT|LAB|PTR|SUB|SUB_|thunk_FUN)_[0-9a-fA-F]{4,}\b|\bundefined[1-8]\b|\bundefined\s*\*'
                                    r'|\b(?:param|local|Stack)_[0-9a-fA-F]+\b|\b[iupcbl]Var\d+\b'
                                    r'|\bin_[A-Z]{2,3}\b|\b(?:unaff|extraout)_\w+')),
    ('hex-run', re.compile(r'(?<![0-9A-Za-z@])[0-9a-fA-F]{32,}(?![0-9A-Za-z])'
                           r'|(?<![0-9A-Za-z])(?:[0-9a-fA-F]{2}[ ,:-]){15}[0-9a-fA-F]{2}(?![0-9A-Za-z])'
                           r'|(?:0x[0-9a-fA-F]{1,2}\s*,\s*){7}0x[0-9a-fA-F]{1,2}\b|(?:\\x[0-9a-fA-F]{2}){8,}')),
    ('asm-directive', re.compile(r'\b(?:__emit|__asm__|__asm|_asm)\b|\basm\s*[({]'
                                 r'|#\s*pragma\s+(?:code_seg|section|comment\s*\(\s*linker)'
                                 r'|__declspec\s*\(\s*(?:naked|allocate)')),
    ('private-path', re.compile(r'/Users/|/home/\w|[A-Za-z]:[\\/]+Users[\\/]|/private/var/|/Volumes/', re.I)),
)
# A 40-digit revision or 64-digit digest in a comment is a provenance pin, not a byte dump.
PINNED_REVISION = re.compile(r'(?<![0-9A-Za-z])[0-9a-f]{40}(?:[0-9a-f]{24})?(?![0-9A-Za-z])')
COMMENT = re.compile(r'^\s*(?://|\*|/\*)')
INCLUDE = re.compile(r'^\s*#\s*include\s*([<"])([^>"]*)[>"]')


def include_problem(line, path=None, headers=STANDARD_HEADERS):
    m = INCLUDE.match(line)
    if not m:
        return False
    kind, target = m.groups()
    parts = PurePosixPath(target).parts
    if '\\' in target or ':' in target or target.startswith('/') or not re.fullmatch(r'[A-Za-z0-9_./-]+', target):
        return True
    if '..' in parts and kind == '"' and path:
        # Relative hops are fine while the result stays under reconstruction/.
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(path), target))
        return not resolved.startswith('reconstruction/') or '..' in resolved.split('/')
    if not parts or any(p in ('.', '..') for p in parts):
        return True
    if kind == '<':
        return target not in headers and not target.endswith('.h')
    return not target.endswith('.h')


def scan_line(line, private=(), path=None):
    scanned = PINNED_REVISION.sub('', line) if COMMENT.match(line) else line
    hits = [code for code, rx in RULES if rx.search(scanned)]
    if include_problem(line, path):
        hits.append('include-outside-roots')
    low = line.lower()
    if any(name in low for name in private):
        hits.append('private-name')
    return hits


def added_lines(diff):
    """Yield (file, new line number, text) for each added line of a zero-context unified diff."""
    name, number = None, 0
    for raw in diff.splitlines():
        if raw.startswith('+++ '):
            name = raw[4:].removeprefix('b/')
        elif raw.startswith('@@'):
            m = re.search(r'\+(\d+)', raw)
            number = int(m.group(1)) if m else 0
        elif raw.startswith('+') and name and name != '/dev/null':
            yield name, number, raw[1:]
            number += 1
        elif raw.startswith(' '):
            number += 1


def scan_diff(diff, private=()):
    """Return sorted (file, line, code); file names that are not plain paths are replaced by an index."""
    found, aliases = [], {}
    for name, number, text in added_lines(diff):
        for code in scan_line(text, private, name):
            if not re.fullmatch(r'[A-Za-z0-9_./-]+', name):
                name = '<file %d>' % aliases.setdefault(name, len(aliases) + 1)
            found.append((name, number, code))
    return sorted(set(found))


def load_private(path):
    try:
        return tuple(l.strip().lower() for l in Path(path).read_text().splitlines() if len(l.strip()) >= 3)
    except OSError:
        return ()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base')
    p.add_argument('--head')
    p.add_argument('--diff', type=Path, help='read a unified diff from a file ("-" for stdin) instead of git')
    p.add_argument('--private-list', type=Path, default=PRIVATE_LIST)
    a = p.parse_args(argv)
    if a.diff:
        diff = sys.stdin.read() if str(a.diff) == '-' else a.diff.read_text(errors='replace')
    elif a.base and a.head:
        diff = subprocess.run(['git', 'diff', '--no-renames', '--no-color', '-U0', '--diff-algorithm=minimal',
                               a.base + '...' + a.head, '--'], cwd=ROOT, capture_output=True, check=True
                              ).stdout.decode('utf-8', 'replace')
    else:
        p.error('give --base and --head, or --diff')
    hits = scan_diff(diff, load_private(a.private_list))
    for name, number, code in hits:
        print('%s:%d %s' % (name, number, code))
    print('leakgrep: %d hit(s)' % len(hits))
    return int(bool(hits))


if __name__ == '__main__':
    sys.exit(main())
