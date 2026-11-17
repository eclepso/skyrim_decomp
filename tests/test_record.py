"""tools/record.py: one function's rows written directly, validator-gated, idempotent, push retried."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
sys.path.insert(0, str(ROOT / 'tools'))
import build_index  # noqa: E402
import record  # noqa: E402
from check import validate  # noqa: E402
from test_match_gate import GateFixture, RECORD, REVIEW  # noqa: E402

OTHER = {'id': 'synthetic-fixture-0x3000', 'build_id': 'synthetic-fixture', 'rva': 0x3000, 'size': 8,
         'status': 'mapped', 'name': 'Other', 'name_origin': 'GUESS', 'owner': 'test',
         'evidence': 'findings/synthetic.md'}
BLOB = b'{"leak": "no"}'


class RecordTests(GateFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        (self.root / REVIEW).unlink()
        self.fn['status'] = 'mapped'
        self.data['functions'].append(dict(OTHER))
        self.save()
        build_index.write_index(self.data, self.root)

    def save(self):
        self.write('data/progress.json', json.dumps(self.data, indent=2, ensure_ascii=False) + '\n')
        self.write('builds/target.json', json.dumps(self.target, indent=2) + '\n')

    def apply(self, rvas=None, **kw):
        return record.apply(self.root, 'synthetic-fixture', rvas or [self.fn['rva']], BLOB,
                            model='gpt-6.1-terra', task_id='pr-bot-1-abcd', **kw)

    def test_rows_point_at_their_own_report_and_validate(self):
        out = self.apply()
        self.assertEqual(out['recorded'], [self.fn['rva']])
        data = json.loads((self.root / 'data/progress.json').read_text())
        row = data['functions'][0]
        self.assertEqual((row['status'], row['report'], row['evidence']), ('matched', RECORD, RECORD))
        self.assertEqual(data['functions'][1], OTHER)
        validate(data, self.target, self.root)
        review = json.loads((self.root / REVIEW).read_text())
        self.assertEqual((review['verdict'], review['review_kind'], review['reviewer_model']),
                         ('approve', 'full', 'gpt-6.1-terra'))

    def test_index_patch_equals_full_render(self):
        self.apply()
        data = json.loads((self.root / 'data/progress.json').read_text())
        self.assertEqual((self.root / build_index.INDEX).read_text(), build_index.render_index(data, self.root))

    def test_validator_refusal_leaves_everything_untouched(self):
        before = (self.root / 'data/progress.json').read_bytes()
        self.write('reconstruction/synthetic/SyntheticSum.h', 'int SyntheticAddOne(int);\nint drift;\n')
        out = self.apply()
        self.assertEqual(out['recorded'], [])
        self.assertIn(self.fn['rva'], out['refused'])
        self.assertEqual((self.root / 'data/progress.json').read_bytes(), before)
        self.assertFalse((self.root / REVIEW).exists())

    def test_unknown_and_unrecorded_functions_are_refused_not_invented(self):
        out = self.apply([0x9999, 0x3000])
        self.assertEqual(out['recorded'], [])
        self.assertEqual(set(out['refused']), {0x9999, 0x3000})

    def test_second_run_is_a_no_op(self):
        self.apply()
        snapshot = (self.root / 'data/progress.json').read_bytes()
        again = self.apply()
        self.assertEqual(again['recorded'], [])
        self.assertEqual(again['refused'][self.fn['rva']], 'already matched')
        self.assertEqual((self.root / 'data/progress.json').read_bytes(), snapshot)


    def test_grown_unit_rebinds_an_already_matched_function_and_a_failure_restores_it(self):
        self.apply()
        # A later stacked PR grows the unit: the digest changes, the old approval is stale.
        old_review = (self.root / REVIEW).read_bytes()
        self.write('reconstruction/synthetic/SyntheticSum.h', 'int SyntheticAddOne(int);\n')
        self.assertEqual(self.apply()['refused'][self.fn['rva']], 'already matched')
        self.assertEqual((self.root / REVIEW).read_bytes(), old_review)


class PushRetryTests(unittest.TestCase):
    def test_non_fast_forward_is_fetched_rebased_and_pushed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            def g(cwd, *a):
                return subprocess.run(['git', '-C', str(cwd), *a], check=True, capture_output=True, text=True).stdout
            subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(tmp / 'o.git')], check=True)
            for name in ('a', 'b'):
                subprocess.run(['git', 'clone', '-q', str(tmp / 'o.git'), str(tmp / name)], check=True, capture_output=True)
                g(tmp / name, 'config', 'user.email', 't@example.invalid')
                g(tmp / name, 'config', 'user.name', 't')
            (tmp / 'a/f').write_text('1\n')
            g(tmp / 'a', 'add', 'f'); g(tmp / 'a', 'commit', '-qm', 'base'); g(tmp / 'a', 'push', '-q', 'origin', 'HEAD:main')
            g(tmp / 'b', 'pull', '-q', 'origin', 'main')
            (tmp / 'a/g').write_text('x\n')
            g(tmp / 'a', 'add', 'g'); g(tmp / 'a', 'commit', '-qm', 'race'); g(tmp / 'a', 'push', '-q', 'origin', 'HEAD:main')
            calls = []
            def fake(root, *a, **k):
                calls.append(1)
                (Path(root) / 'h').write_text('rec\n')
                return {'recorded': [1], 'refused': {}, 'files': ['h']}
            real = record.apply
            record.apply = fake
            try:
                out = record.record_and_push(tmp / 'b', 'x', [1], b'', 'Record', model='m', task_id='t')
            finally:
                record.apply = real
            self.assertTrue(out['pushed'])
            self.assertEqual(g(tmp / 'o.git', 'log', '--format=%s', 'main').split(), ['Record', 'race', 'base'])
            self.assertEqual(len(calls), 1)


if __name__ == '__main__':
    unittest.main()
