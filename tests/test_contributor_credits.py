"""Original synthetic accepted credit, duplicate submissions and public strike policy."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_leaderboard as board
import contributor_standing as standing
import ci_target_hash_check as ci


class Credits(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'reports').mkdir()

    def fixture(self, record):
        (self.root / 'reports/a.json').write_text(json.dumps(record))
        fn = dict(id='synthetic-0x1000', build_id='synthetic', rva=4096, size=23,
                  status='matched', report='reports/a.json')
        return dict(functions=[fn])

    def test_p161_alternates_retries_case_and_revocations(self):
        record = dict(matchers=[dict(handle='Alice', model='gpt-6.1-sol', source_digest='a' * 64),
                                dict(handle='@ALICE', model='gpt-6.1-sol', source_digest='b' * 64),
                                dict(handle='bob', model='none', source_digest='c' * 64)])
        data = self.fixture(record)
        data['functions'].append(copy.deepcopy(data['functions'][0]))
        rows = board.standings(self.root, data)
        self.assertEqual([(r['contributor'], r['functions'], r['bytes']) for r in rows],
                         [('@alice', 1, 23), ('@bob', 1, 23)])
        for fn in data['functions']:
            fn['status'] = 'mapped'
        self.assertEqual(board.standings(self.root, data), [])

    def test_submitter_agent_and_missing_attribution_fallback(self):
        data = self.fixture(dict(submitter='Alice'))
        self.assertEqual(board.standings(self.root, data)[0]['contributor'], '@alice')
        data = self.fixture(dict(drafter_model='gpt-6.1-sol'))
        self.assertEqual(board.standings(self.root, data)[0]['contributor'], 'project agents (gpt-6.1-sol)')
        data = self.fixture({})
        self.assertIn('Not reported', board.standings(self.root, data)[0]['contributor'])
        data = self.fixture(dict(origin=dict(family='synthetic')))
        self.assertIn('Scripts and tools', board.standings(self.root, data)[0]['contributor'])

    def test_no_emails_or_private_labels_and_tiers(self):
        data = self.fixture(dict(submitter='private@example.invalid', matchers=[
            dict(handle='/Users/private', model='gpt-6.1-sol')]))
        text = board.markdown(board.standings(self.root, data))
        self.assertNotIn('/Users/', text)
        self.assertNotIn('example.invalid', text)
        self.assertEqual([board.tier(n) for n in (0, 9, 10, 99, 100, 999, 1000)],
                         ['Contributor', 'Contributor', '10+', '10+', '100+', '100+', '1,000+'])
        self.assertIn('Contributor leaderboard', board.html([]))

    def events(self):
        return dict(schema=1, contributors=dict(alice=dict(false_claims=[
            dict(pr=n, head='a' * 40, rvas=['0x1000'], check_run=n) for n in range(1, 4)], cleared_strikes=0)))

    def test_three_strikes_clear_without_erasing_history_and_validation(self):
        data = standing.validate(self.events())
        self.assertFalse(standing.standing(data, '@ALICE')['auto_merge_eligible'])
        self.assertEqual(standing.standing(data, 'alice')['label'], 'needs maintainer')
        data['contributors']['alice']['cleared_strikes'] = 3
        got = standing.standing(standing.validate(data), 'alice')
        self.assertTrue(got['auto_merge_eligible'])
        self.assertEqual(got['false_claims'], 3)
        for mutation in ('duplicate', 'email', 'clear'):
            bad = self.events()
            if mutation == 'duplicate':
                bad['contributors']['alice']['false_claims'][1]['pr'] = 1
            elif mutation == 'email':
                bad['contributors']['private@example.invalid'] = bad['contributors'].pop('alice')
            else:
                bad['contributors']['alice']['cleared_strikes'] = 4
            with self.assertRaises(ValueError):
                standing.validate(bad)

    def test_only_explicit_completed_hash_mismatches_are_strikes(self):
        report = dict(kind='target-hash-check', toolset='MATCH', functions=[
            dict(rva='0x1000', result='mismatch'), dict(rva='0x2000', result='no-target'),
            dict(rva='0x3000', result='mismatch', reason='compile-failed'),
            dict(rva='0x4000', result='hash-match')])
        self.assertEqual(standing.false_claims(report, ['0x1000', '0x2000', '0x3000', '0x4000']), ['0x1000'])
        self.assertFalse(standing.false_claims(report, []))
        self.assertFalse(standing.false_claims(dict(report, error='setup'), ['0x1000']))
        for row in report["functions"]:
            row["unit"] = "reconstruction/synthetic/Fixture.cpp"
        text = ci.summary_text(report)
        self.assertIn('PASS (hash only)', text)
        self.assertIn('FAIL', text)
        self.assertIn('UNVERIFIED', text)

    def test_public_record_combines_accepted_credit_with_strikes(self):
        data = self.fixture(dict(submitter='alice'))
        (self.root / 'data').mkdir()
        (self.root / standing.LEDGER).write_text(json.dumps(self.events()))
        rows = board.standings(self.root, data)
        record = board.public_records(self.root, rows)['contributors']['alice']
        self.assertEqual((record['verified_matches'], record['matched_bytes'], record['false_claims'], record['strikes']),
                         (1, 23, 3, 3))
        self.assertFalse(record['auto_merge_eligible'])
        data['functions'][0]['status'] = 'mapped'
        record = board.public_records(self.root, board.standings(self.root, data))['contributors']['alice']
        self.assertEqual((record['verified_matches'], record['strikes']), (0, 3))

    def test_ci_compiles_unbound_units_and_reuses_one_object_per_recipe(self):
        recipe = 'reconstruction/recipes/synthetic.json'
        (self.root / recipe).parent.mkdir(parents=True)
        (self.root / recipe).write_text(json.dumps(dict(sdk='synthetic-sdk')))
        obj = self.root / 'synthetic.obj'
        obj.write_bytes(b'original synthetic placeholder')
        refs = [dict(unit='reconstruction/synthetic/Fixture.cpp', rva=None, symbol=None, recipe=recipe),
                dict(unit='reconstruction/synthetic/Fixture.cpp', rva=4096, symbol='synthetic', recipe=recipe)]
        manifest = dict(functions=[], recipe_sha256={recipe: 'a' * 64})
        bindir = self.root / 'a/b/c/d/e/f/g'
        with patch.object(ci.contrib, 'sdk_include_dirs', return_value=(None, [self.root / 'synthetic-sdk/include'])), \
                patch.object(ci.contrib, 'compile_unit', return_value=dict(object=obj)) as compile_:
            rows = ci.compile_requests(self.root, self.root, refs, bindir, self.root / 'work', manifest)
        self.assertEqual(compile_.call_count, 1)
        self.assertEqual([row['result'] for row in rows], ['no-target', 'no-target'])
        self.assertTrue(all(row['reason'] == 'published-target-or-binding-unavailable' for row in rows))

    def test_recording_cli_requires_exact_head_and_duplicate_pr_is_refused(self):
        report = self.root / 'trusted.json'
        report.write_text(json.dumps(dict(kind='target-hash-check', toolset='MATCH', head_sha='a' * 40,
                                         functions=[dict(rva='0x1000', result='mismatch')])))
        (self.root / 'data').mkdir()
        argv = ['--author', 'alice', '--record', str(report), '--head', 'a' * 40,
                '--pr', '1', '--check-run', '7', '--claimed', '0x1000']
        with patch.object(standing, 'ROOT', self.root), patch('builtins.print'):
            self.assertEqual(standing.main(argv), 0)
            with self.assertRaises(ValueError):
                standing.main(argv)
            with self.assertRaises(SystemExit):
                standing.main([value if value != 'a' * 40 else 'b' * 40 for value in argv])
            self.assertEqual(standing.main(['--author', 'alice', '--clear']), 0)
        got = standing.standing(standing.load(self.root), 'alice')
        self.assertEqual((got['strikes'], got['false_claims']), (0, 1))


class SiteCreditRendering(unittest.TestCase):
    def test_site_build_preserves_tracked_contributor_views(self):
        import build_site as site
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'site').mkdir()
            (root / 'site/style.css').write_text('/* original synthetic style */')
            (root / 'data').mkdir()
            (root / standing.LEDGER).write_text(json.dumps(dict(schema=1, contributors={})))
            original = {'LEADERBOARD.md': b'# Original tracked snapshot\n',
                        'data/contributors.json': b'{"schema":1,"contributors":{},"snapshot":"original"}\n'}
            for name, data in original.items():
                (root / name).write_bytes(data)
            with (patch.object(site, 'ROOT', root),
                  patch.object(site, 'validated_data', return_value={'functions': []}),
                  patch.object(site.subprocess, 'check_output', side_effect=[b'synthetic-revision', b'']),
                  patch.object(site.build_model_trend, 'GitBlobs'),
                  patch.object(site.build_model_trend, 'history', return_value=([], [])),
                  patch.object(site.build_model_trend, 'render', return_value='<svg/>'),
                  patch.object(site.build_model_trend, 'render_cumulative', return_value='<svg/>'),
                  patch.object(site, 'render', return_value='<main>synthetic report</main>'),
                  patch.object(site, 'render_join', return_value='<main>synthetic guide</main>'),
                  patch('builtins.print')):
                site.main()
            for name, data in original.items():
                self.assertEqual((root / name).read_bytes(), data)
            self.assertIn('Contributor leaderboard', (root / 'dist/leaderboard.html').read_text())

if __name__ == '__main__':
    unittest.main()
