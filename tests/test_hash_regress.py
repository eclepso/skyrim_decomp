import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import ci_target_hash_check as check  # noqa: E402


def row(unit, rva, result):
    return dict(unit=unit, rva=rva, result=result)


class Classify(unittest.TestCase):
    def status(self, head, base):
        rows = check.classify([row('u.cpp', '0x10', head)], [row('u.cpp', '0x10', base)] if base else [])
        return rows[0]['status']

    def test_pass_at_head_is_pass_whatever_the_base_was(self):
        for base in ('hash-match', 'mismatch', None):
            self.assertEqual(self.status('hash-match', base), 'pass')

    def test_passed_at_base_and_fails_at_head_is_a_regression(self):
        self.assertEqual(self.status('mismatch', 'hash-match'), 'regressed')

    def test_debt_that_failed_at_base_does_not_block(self):
        self.assertEqual(self.status('mismatch', 'mismatch'), 'preexisting-fail')

    def test_new_function_that_fails_is_reported_not_a_regression(self):
        self.assertEqual(self.status('mismatch', None), 'fail')

    def test_unverifiable_rows_are_not_failures(self):
        self.assertEqual(self.status('no-target', 'hash-match'), 'unverified')

    def test_rows_are_matched_by_unit_and_rva(self):
        rows = check.classify([row('a.cpp', '0x10', 'mismatch')], [row('b.cpp', '0x10', 'hash-match')])
        self.assertEqual(rows[0]['status'], 'fail')

    def test_only_status_codes_are_added(self):
        out = check.classify([row('u.cpp', '0x10', 'mismatch')], [])[0]
        self.assertEqual(set(out) - {'unit', 'rva', 'result'}, {'status', 'base'})


if __name__ == '__main__':
    unittest.main()
