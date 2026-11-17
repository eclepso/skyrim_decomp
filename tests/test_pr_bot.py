"""tools/pr_bot.py decisions and orchestration, with every host, model and GitHub call stubbed."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import pr_bot  # noqa: E402

HEAD = 'a' * 40
BASE = 'b' * 40
PR = {'number': 7, 'headRefOid': HEAD, 'author': {'login': 'alice'}}
GOOD = json.dumps({'leak': 'no', 'functions': {'0x10': {'verdict': 'approve', 'ground': 'none'},
                                                '0x20': {'verdict': 'approve', 'ground': 'none'}}})


class DecisionTests(unittest.TestCase):
    def table(self, h1, h2, rv, **kw):
        return pr_bot.decide([0x10], {0x10: h1}, {0x10: h2}, {0x10: rv}, **kw)

    def test_matched_needs_both_hosts_and_the_review(self):
        self.assertEqual(self.table('pass', 'pass', 'approve')['verdicts'][0x10], 'matched')
        self.assertEqual(self.table('fail', 'pass', 'approve')['verdicts'][0x10], 'fail:host1')
        self.assertEqual(self.table('pass', 'fail', 'approve')['verdicts'][0x10], 'fail:host2')
        self.assertEqual(self.table('pass', 'pass', 'reject')['verdicts'][0x10], 'fail:review')
        self.assertEqual(self.table('pass', None, 'approve')['verdicts'][0x10], 'fail:missing')
        self.assertTrue(self.table('pass', 'pass', 'approve')['merge'])
        self.assertFalse(self.table('pass', 'pass', 'reject')['merge'])

    def test_leak_or_grep_hit_blocks_the_whole_pr(self):
        for kw in ({'leak': 'yes'}, {'leak_hits': ['R1']}):
            d = pr_bot.decide([0x10, 0x20], {0x10: 'pass', 0x20: 'pass'}, {0x10: 'pass', 0x20: 'pass'},
                              {0x10: 'approve', 0x20: 'approve'}, **kw)
            self.assertEqual((d['blocked'], d['merge']), ('leak', False))
            self.assertEqual(set(d['verdicts'].values()), {'blocked'})

    def test_regression_blocks_but_preexisting_debt_does_not(self):
        d = pr_bot.decide([0x10, 0x20], {0x10: 'pass', 0x20: 'regressed'}, {0x10: 'pass', 0x20: 'pass'},
                          {0x10: 'approve', 0x20: 'approve'})
        self.assertEqual((d['blocked'], d['merge']), ('regression', False))
        d = pr_bot.decide([0x10, 0x20], {0x10: 'pass', 0x20: 'preexisting-fail'}, {0x10: 'pass', 0x20: 'fail'},
                          {0x10: 'approve', 0x20: 'reject'})
        self.assertEqual(d['verdicts'], {0x10: 'matched', 0x20: 'debt'})
        self.assertIsNone(d['blocked'])
        self.assertTrue(d['merge'])
        self.assertNotIn('0x20', pr_bot.comment_body(HEAD, d))

    def test_a_bad_review_answer_never_approves(self):
        self.assertEqual(pr_bot.parse_review('nonsense', [0x10]), ('yes', {}))
        leak, out = pr_bot.parse_review('x ' + GOOD, [0x10, 0x30])
        self.assertEqual((leak, out), ('no', {0x10: 'approve', 0x30: 'reject'}))


class ScopeAndMergeTests(unittest.TestCase):
    def test_scope_rejects_anything_outside_reconstruction(self):
        ok = [{'filename': 'reconstruction/a/B.cpp', 'status': 'added'}]
        self.assertIsNone(pr_bot.scope_problem(ok))
        for bad in ({'filename': '.github/workflows/x.yml'}, {'filename': 'tools/x.py'},
                    {'filename': 'reconstruction/../tools/x.py'}, {'filename': 'data/progress.json'},
                    {'filename': 'reconstruction/a.cpp', 'previous_filename': 'tools/old.py'}):
            self.assertEqual(pr_bot.scope_problem(ok + [bad]), 'scope')
        self.assertEqual(pr_bot.scope_problem([]), 'empty')

    def test_merge_command_pins_the_head_and_uses_a_bot_message(self):
        subject, body = pr_bot.squash_message(7, 'alice', 99, [0x20, 0x10])
        argv = pr_bot.merge_command(7, HEAD, subject, body)
        self.assertEqual(argv[argv.index('--match-head-commit') + 1], HEAD)
        self.assertIn('--squash', argv)
        self.assertEqual(subject, 'Reconstruct 2 functions (0x10, 0x20) (#7)')
        self.assertIn('Co-authored-by: alice <99+alice@users.noreply.github.com>', body)


class DropLandedTests(unittest.TestCase):
    def test_only_files_that_differ_from_main_remain(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            def git(*a):
                return subprocess.run(['git', '-C', tmp, *a], check=True, capture_output=True, text=True).stdout.strip()
            git('init', '-q', '-b', 'main')
            git('config', 'user.email', 't@example.invalid'); git('config', 'user.name', 't')
            (repo / 'reconstruction').mkdir()
            (repo / 'reconstruction/low.cpp').write_text('1\n')
            git('add', '.'); git('commit', '-qm', 'main'); git('update-ref', 'refs/remotes/origin/main', 'HEAD')
            (repo / 'reconstruction/high.cpp').write_text('2\n')
            git('add', '.'); git('commit', '-qm', 'head')
            head = git('rev-parse', 'HEAD')
            bot = pr_bot.Bot(root=repo, work=repo / 'w')
            files = [{'filename': 'reconstruction/low.cpp', 'status': 'added'},
                     {'filename': 'reconstruction/high.cpp', 'status': 'added'}]
            self.assertEqual([f['filename'] for f in bot.drop_landed(head, files)], ['reconstruction/high.cpp'])


class FakeBot(pr_bot.Bot):
    def __init__(self, work, files=None, h1=None, h2=None, review=GOOD, grep=(False, []), **kw):
        super().__init__(root=ROOT, work=work, **kw)
        self.calls, self.files = [], files or [{'filename': 'reconstruction/a/B.cpp', 'status': 'added'}]
        self.h1 = h1 or {0x10: 'pass', 0x20: 'pass'}
        self.h2 = h2 or {0x10: 'pass', 0x20: 'pass'}
        self.review_text, self.grep = review, grep
        self.merge_ok = True
        self.landed = None

    def run(self, argv, **kw):
        argv = [str(a) for a in argv]
        self.calls.append(argv)
        out = BASE.encode() if argv[:2] == ['git', 'merge-base'] else b''
        code = 1 if argv[:3] == ['gh', 'pr', 'merge'] and not self.merge_ok else 0
        return subprocess.CompletedProcess(argv, code, out, b'')

    def gh_json(self, *a):
        return {'id': 99}

    def changed_files(self, number):
        self.calls.append(['changed_files'])
        return self.files

    def prepare_tree(self, base):
        pass

    def overlay(self, head, files):
        pass

    def drop_landed(self, head, files, ref=None):
        self.calls.append(['drop_landed'])
        return self.files if self.landed is None else self.landed

    def units(self, files):
        return {'reconstruction/a/B.cpp': [0x10, 0x20]}

    def leakgrep(self, base, head):
        return self.grep

    def review(self, *a):
        self.calls.append(['review'])
        return self.review_text

    def mac_compare(self, units, tag):
        self.calls.append(['mac'])
        return dict(self.h2)

    def host1(self, number, head, functions):
        return dict(self.h1)

    def classify_debt(self, host2, *a):
        return host2

    def build_records(self, *a):
        return Path('/nonexistent')

    def record(self, pr, state, rvas):
        self.calls.append(['record', rvas])
        state.set('recorded', True)

    def seen(self, *prefix):
        return [c for c in self.calls if c[:len(prefix)] == list(prefix)]


class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)

    def test_all_pass_merges_once_records_and_survives_a_rerun(self):
        bot = FakeBot(self.work)
        out = bot.process(PR)
        self.assertEqual(out['verdicts'], {'0x10': 'matched', '0x20': 'matched'})
        self.assertEqual(len(bot.seen('gh', 'pr', 'merge')), 1)
        self.assertEqual(len(bot.seen('record')), 1)
        before = len(bot.calls)
        bot.process(PR)
        self.assertEqual(len(bot.calls), before)

    def test_rerun_after_a_crash_resumes_without_repeating_paid_work(self):
        bot = FakeBot(self.work)
        original = bot.host1
        def boom(*a):
            raise pr_bot.Stop('hash check has not finished')
        bot.host1 = boom
        with self.assertRaises(pr_bot.Stop):
            bot.process(PR)
        bot.host1 = original
        bot.process(PR)
        self.assertEqual((len(bot.seen('review')), len(bot.seen('mac'))), (1, 1))
        self.assertEqual(len(bot.seen('gh', 'pr', 'merge')), 1)

    def test_scope_rejection_never_compiles_reviews_or_merges(self):
        bot = FakeBot(self.work, files=[{'filename': '.github/workflows/pr-check.yml', 'status': 'modified'}])
        out = bot.process(PR)
        self.assertEqual(out['blocked'], 'scope')
        self.assertEqual((bot.seen('review'), bot.seen('mac'), bot.seen('gh', 'pr', 'merge')), ([], [], []))
        self.assertEqual(len(bot.seen('gh', 'pr', 'comment')), 1)

    def test_grep_hit_blocks_before_any_model_or_host_call(self):
        bot = FakeBot(self.work, grep=(True, ['LG01']))
        out = bot.process(PR)
        self.assertEqual(out['blocked'], 'leak')
        self.assertEqual((bot.seen('review'), bot.seen('mac'), bot.seen('gh', 'pr', 'merge')), ([], [], []))
        self.assertIn('LG01', bot.seen('gh', 'pr', 'comment')[0][-1])

    def test_debt_function_does_not_block_the_others(self):
        bot = FakeBot(self.work, h1={0x10: 'pass', 0x20: 'preexisting-fail'}, h2={0x10: 'pass', 0x20: 'fail'})
        out = bot.process(PR)
        self.assertEqual(out['verdicts'], {'0x10': 'matched', '0x20': 'debt'})
        self.assertEqual(len(bot.seen('gh', 'pr', 'merge')), 1)
        self.assertEqual(bot.seen('gh', 'pr', 'comment'), [])

    def test_partial_pass_merges_and_comments_only_on_the_failure(self):
        bot = FakeBot(self.work, h2={0x10: 'pass', 0x20: 'fail'})
        bot.process(PR)
        self.assertEqual(len(bot.seen('gh', 'pr', 'merge')), 1)
        body = bot.seen('gh', 'pr', 'comment')[0][-1]
        self.assertIn('0x20', body)
        self.assertNotIn('0x10:', body)

    def test_nothing_passing_does_not_merge(self):
        bot = FakeBot(self.work, review=json.dumps({'leak': 'no', 'functions': {}}))
        bot.process(PR)
        self.assertEqual(bot.seen('gh', 'pr', 'merge'), [])

    def test_dry_run_has_no_side_effects(self):
        bot = FakeBot(self.work, dry_run=True)
        out = bot.process(PR)
        self.assertTrue(out['merge'])
        self.assertEqual((bot.seen('gh', 'pr', 'merge'), bot.seen('gh', 'pr', 'comment'), bot.seen('record')), ([], [], []))

    def test_stacked_pr_whose_content_already_landed_is_closed_not_merged(self):
        bot = FakeBot(self.work)
        bot.landed = []
        out = bot.process(PR)
        self.assertFalse(out['merge'])
        self.assertEqual((bot.seen('mac'), bot.seen('review'), bot.seen('gh', 'pr', 'merge')), ([], [], []))
        self.assertEqual(len(bot.seen('gh', 'pr', 'close')), 1)

    def test_refused_merge_starts_over(self):
        bot = FakeBot(self.work)
        bot.merge_ok = False
        with self.assertRaises(pr_bot.Stop):
            bot.process(PR)
        self.assertEqual(bot.seen('record'), [])
        bot.merge_ok = True
        bot.process(PR)
        self.assertEqual(len(bot.seen('record')), 1)


if __name__ == '__main__':
    unittest.main()
