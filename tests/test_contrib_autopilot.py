
"""Contributor autopilot using only original synthetic source, fake GitHub and fake verifiers."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'tools/verifier'))
import contrib_autopilot as ap
import contrib_screen as screen
import unit_build


GOOD = b'''// Original synthetic fixture; source https://example.org/types.
#pragma once
#include <cstdint>
class Synth { public: int value; };
'''

class FreshWinePreparation(unittest.TestCase):
    def test_existing_runner_prepares_toolchain_afresh_and_fetches_private_evidence(self):
        import wine_confirm
        task = dict(dir=Path('/synthetic/task'))
        host = dict(backend='local', loader='wine', host_id='mac-wine')
        with patch.object(wine_confirm.pipeline, 'load_task', return_value=task), \
                patch.object(wine_confirm.pipeline, 'unit_manifest', return_value=(['synthetic.cpp'], [])), \
                patch.object(wine_confirm.runners, 'for_attempt', return_value=host), \
                patch.object(wine_confirm.runners, 'AgentHost') as factory:
            factory.return_value.run.return_value = (0, None)
            self.assertEqual(wine_confirm.run(task['dir']), 0)
        self.assertIs(factory.call_args.kwargs['fresh_prep'], True)
        factory.return_value.fetch.assert_called_once_with(task['dir'] / 'confirm/mac-wine')

    def test_native_first_host_prepares_and_fetches(self):
        import wine_confirm
        task = dict(dir=Path('/synthetic/task'))
        host = dict(backend='ssh', loader='native', host_id='synthetic-native')
        with patch.object(wine_confirm.pipeline, 'load_task', return_value=task), \
                patch.object(wine_confirm.pipeline, 'unit_manifest', return_value=([], [])), \
                patch.object(wine_confirm.runners, 'for_attempt', return_value=host), \
                patch.object(wine_confirm.runners, 'AgentHost') as factory:
            factory.return_value.run.return_value = (0, None)
            self.assertEqual(wine_confirm.run(task['dir']), 0)
            self.assertTrue(factory.call_args.kwargs['fresh_prep'])
            factory.return_value.fetch.assert_called_once_with(task['dir'] / 'confirm/synthetic-native')

    def test_unsupported_or_missing_first_host_never_starts_a_worker(self):
        import wine_confirm
        for host in (None, dict(backend='ssh', loader='wine', host_id='unsupported')):
            with self.subTest(host=host), \
                    patch.object(wine_confirm.pipeline, 'load_task', return_value=dict(dir=Path('/synthetic/task'))), \
                    patch.object(wine_confirm.pipeline, 'unit_manifest', return_value=([], [])), \
                    patch.object(wine_confirm.runners, 'for_attempt', return_value=host), \
                    patch.object(wine_confirm.runners, 'AgentHost') as factory:
                with self.assertRaises(wine_confirm.runners.RunnerError):
                    wine_confirm.run(Path('/synthetic/task'))
                factory.assert_not_called()


def pr(number=1, author='contributor', head='a' * 40, paths=('reconstruction/synth/Synth.cpp',)):
    return dict(number=number, author=dict(login=author), headRefOid=head, isDraft=False,
                baseRefName='main', files=[dict(path=p) for p in paths])


class Screen(unittest.TestCase):
    def test_ordinary_headers_and_programmer_cpp(self):
        self.assertEqual(screen.screen(GOOD, 'Synth.h'), [])
        self.assertEqual(screen.screen(b'#pragma pack(push, 8)\n#pragma warning(disable: 4100)\n'
                                       b'#define COUNT 4\nint values[COUNT];\n#pragma pack(pop)\n', 'Synth.h'), [])

    def test_malicious_pattern_corpus(self):
        corpus = [
            b'#include "/etc/passwd"', b'#include "../private.h"', b'#include <../../private.h>',
            b'#include "Z:\\private.h"', b'#include HEADER', b'#include_next <cstdint>',
            b'# /**/ include "private.h"', b'%:include "private.h"', b'??=include "private.h"',
            b'#import "plugin.dll"', b'#pragma comment(lib, "plugin")', b'#pragma message("leak")',
            b'#pragma include_alias("a", "b")', b'#pragma code_seg("evil")', b'#pragma once; evil',
            b'__asm { ret }', b'_asm nop', b'asm("nop")', b'__asm__ ("nop")',
            b'__declspec(allocate("evil")) int x;', b'__declspec /*x*/ ( allocate("evil")) int x;',
            b'__pragma(comment(lib,"evil"))', b'_Pragma("once")', b'#define JOIN(a,b) a ## b',
            b'#de\\\nfine ASM __as\\\nm', b'char *path = "/etc/passwd";',
            b'#define PATH "../outside"', b'char *p="C:private";', b'char *p="\\x2e\\x2e";',
            b'char *p="\\057etc";', b'#line 1 "/etc/passwd"', b'R"(hidden)"',
            b'// \x00', b'// \x1b[31m', b'// \x7f', b'\xff',
            '// \u202e hidden'.encode(), '// \u200b hidden'.encode(),
        ]
        for blob in corpus:
            with self.subTest(blob=blob):
                self.assertTrue(screen.screen(blob, 'Synth.cpp'))

    def test_line_size_and_template_caps(self):
        for blob, code in [(b'x' * (screen.MAX_BYTES + 1), 'file-size-cap'),
                           (b'\n' * (screen.MAX_LINES + 1), 'line-count-cap'),
                           (b'x' * (screen.MAX_LINE + 1), 'line-length-cap'),
                           (b'T<' * (screen.MAX_DEPTH + 1), 'template-or-expression-depth'),
                           (b'#if X\n' * (screen.MAX_DEPTH + 1), 'preprocessor-depth')]:
            with self.subTest(code=code):
                self.assertIn(code, screen.screen(blob, 'Synth.cpp'))

    def test_macro_depth_cycles_and_exponential_expansion(self):
        self.assertIn('macro-depth-or-cycle', screen.screen(b'#define A B\n#define B A\n', 'Synth.h'))
        nested = '\n'.join(f'#define M{i} M{i+1}' for i in range(screen.MAX_DEPTH + 2))
        self.assertIn('macro-depth-or-cycle', screen.screen(nested.encode(), 'Synth.h'))
        expansion = '#define M0 x\n' + '\n'.join(f'#define M{i} M{i-1} M{i-1}' for i in range(1, 20))
        self.assertIn('macro-expansion-cap', screen.screen(expansion.encode(), 'Synth.h'))
        many = '\n'.join(f'#define M{i} {i}' for i in range(screen.MAX_MACROS + 1))
        self.assertIn('macro-count-cap', screen.screen(many.encode(), 'Synth.h'))

    def test_include_roots_checked_transitively(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unit = root / 'reconstruction/synth'
            unit.mkdir(parents=True)
            (unit / 'Synth.cpp').write_text('#include "Synth.h"\n')
            (unit / 'Synth.h').write_bytes(GOOD)
            self.assertEqual(screen.screen_tree(root, 'reconstruction/synth/Synth.cpp'), [])
            (unit / 'Synth.h').write_text('#include <intrin.h>\n')
            self.assertEqual(screen.screen_tree(root, 'reconstruction/synth/Synth.cpp'), [])
            (unit / 'Synth.h').write_text('#include <windows.h>\n')
            self.assertIn('include-outside-roots', screen.screen_tree(root, 'reconstruction/synth/Synth.cpp'))
            other = root / 'tools'
            other.mkdir()
            (other / 'Tool.h').write_text('int secret;\n')
            (unit / 'Synth.h').write_text('#include "tools/Tool.h"\n')
            with self.assertRaises(ValueError):
                screen.screen_tree(root, 'reconstruction/synth/Synth.cpp')

    def test_allowed_community_headers_are_repository_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'reconstruction/synth').mkdir(parents=True)
            (root / 'reconstruction/community').mkdir()
            (root / 'reconstruction/synth/Synth.cpp').write_text('#include <community/Types.h>\n')
            (root / 'reconstruction/community/Types.h').write_text('struct Synth {};\n')
            self.assertEqual(screen.screen_tree(root, 'reconstruction/synth/Synth.cpp'), [])


class Selection(unittest.TestCase):
    def test_scope_is_exact(self):
        self.assertIsNone(ap.selection_problem(pr()['files']))
        for path in ('tools/contrib.py', '.github/workflows/check.yml', 'reconstruction/synth/a.cpp',
                     'reconstruction/synth/Synth.hpp', 'reconstruction/synth/../Synth.cpp',
                     'reconstruction/a/b/Synth.cpp', '/reconstruction/synth/Synth.cpp'):
            self.assertIsNotNone(ap.selection_problem([dict(path=path)]))
        self.assertIsNotNone(ap.selection_problem([]))

    def test_oldest_one_per_contributor_case_insensitive_and_drafts_wait(self):
        rows = [pr(4, 'Alice'), pr(3, 'Bob'), pr(2, 'alice'), dict(pr(1, 'Alice'), isDraft=True)]
        self.assertEqual([p['number'] for p in ap.select_prs(rows)], [2, 3, 4])

    def test_round_robin(self):
        rows = [pr(1, 'A'), pr(2, 'A'), pr(3, 'A'), pr(4, 'B')]
        self.assertEqual([p['author']['login'] for p in ap.select_prs(rows)], ['A', 'B', 'A', 'A'])


class FakeRuntime:
    def __init__(self):
        self.root = Path(tempfile.gettempdir()) / 'synthetic-contributor-standing-unused'
        self.calls, self.messages = [], []
        self.crash = None
        self.unsafe, self.reject, self.scope = False, False, False
        self.intake_errors = []
        self.confirmed = dict(passed=['0x1000', '0x2000'], failed=[])
        self.reviewed = dict(groups=['g1'], failed=[])

    def call(self, name, value):
        self.calls.append(name)
        if self.crash == name:
            raise OSError('simulated crash')
        return copy.deepcopy(value)

    def ci_hash_signal(self, head):
        return dict(kind='target-hash-ci', head_sha=head, state=getattr(self, 'hash_state', 'absent'),
                    advisory=True, acceptance='not-evaluated')

    def fetch(self, pr):
        return self.call('fetch', dict(tree='synthetic', base='b' * 40, files=pr['files'], diff='synthetic'))

    def intake(self, fetched):
        return self.call('intake', self.intake_errors)

    def functions(self, fetched):
        if self.reject:
            raise ap.Rejected('per-PR function cap exceeded')
        return self.call('functions', {'reconstruction/synth/Synth.cpp': [4096, 8192]})

    def ai_screen(self, fetched):
        return self.call('screen', dict(safe=not self.unsafe, reasons=getattr(self, 'screen_reasons', ['suspicious compiler construct'])))

    def discard_screen(self, fetched):
        pass

    def waiting(self, revision, reason):
        revision['waiting_reason'] = reason

    def export(self, fetched, units):
        return self.call('export', ['synthetic-task'])

    def companions(self, fetched):
        return getattr(self, 'accepted_companions', {})

    def confirm(self, fetched, tasks, revision):
        return self.call('confirm', self.confirmed)

    def credit_confirmation(self, fetched, confirmed, revision):
        pass

    def make_groups(self, fetched, confirmed):
        return self.call('groups', ['g1'])

    def reviews(self, fetched, groups, tasks, revision):
        return self.call('reviews', self.reviewed)

    def publish(self, fetched, reviewed, revision):
        revision['enqueued'] = True
        return self.call('publish', dict(commits=['c' * 40], accepted=['0x1000'], dropped=1))

    def finish(self, revision, published):
        self.call('finish', None)

    def feedback(self, revision, key, label, message, **kwargs):
        self.messages.append((key, label, message))


class ResumeAndLimits(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.config = dict(ap.DEFAULTS, daily_compiles=3, daily_reviews=2)
        self.state = ap.State(self.directory, self.config, '2026-01-01')
        self.runtime = FakeRuntime()

    def reload(self):
        self.state = ap.State(self.directory, self.config, '2026-01-01')

    def test_full_synthetic_pipeline_and_idempotent_completion(self):
        result = ap.process(self.runtime, self.state, pr())
        self.assertTrue(result['done'])
        self.assertEqual(self.runtime.calls, ['fetch', 'intake', 'functions', 'screen', 'export',
                                             'confirm', 'groups', 'reviews', 'publish', 'finish'])
        self.reload()
        ap.process(self.runtime, self.state, pr())
        self.assertEqual(self.runtime.calls.count('fetch'), 1)
        self.assertEqual(self.runtime.calls.count('publish'), 1)

    def test_squash_policy_rechecks_a_completed_same_head_history_rejection(self):
        self.config['merge_method'] = 'merge'
        old = self.state.revision(pr())
        old.update(done=True, completed={'fetch': {'problem': 'deterministic screen: include-outside-roots'}})
        self.state.save()
        self.config['merge_method'] = 'squash'
        result = ap.process(self.runtime, self.state, pr())
        self.assertEqual(result['merge_method'], 'squash')
        self.assertIn('reviews', self.runtime.calls)
        self.assertIn('publish', self.runtime.calls)

    def test_enqueued_legacy_method_settles_before_same_head_squash_revision(self):
        self.config['merge_method'] = 'merge'
        self.runtime.crash = 'publish'
        with self.assertRaises(OSError):
            ap.process(self.runtime, self.state, pr())
        self.config['merge_method'] = 'squash'
        self.runtime.crash = None
        settled = ap.process(self.runtime, self.state, pr())
        self.assertEqual(settled['merge_method'], 'merge')
        self.assertTrue(settled['done'])
        self.assertEqual(self.runtime.calls.count('fetch'), 1)
        fresh = ap.process(self.runtime, self.state, pr())
        self.assertEqual(fresh['merge_method'], 'squash')
        self.assertEqual(self.runtime.calls.count('fetch'), 2)

    def test_ci_hash_api_is_exact_head_and_failures_are_only_unavailable(self):
        runtime = ap.Runtime.__new__(ap.Runtime)
        run = dict(id=3, head_sha='a' * 40, app=dict(slug='github-actions'),
                   name='target-hashes', status='completed', conclusion='success')
        runtime.command = Mock(return_value=subprocess.CompletedProcess([], 0,
                               json.dumps([dict(check_runs=[run])]).encode(), b''))
        self.assertEqual(runtime.ci_hash_signal('a' * 40)['state'], 'success')
        self.assertEqual(runtime.ci_hash_signal('b' * 40)['state'], 'absent')
        for error in (ap.Stop('API unavailable'), subprocess.TimeoutExpired('gh', 1)):
            runtime.command.side_effect = error
            got = runtime.ci_hash_signal('a' * 40)
            self.assertEqual(got['state'], 'unavailable')
            self.assertEqual(got['acceptance'], 'not-evaluated')

    def test_fork_approval_notice_does_not_skip_project_confirmation_or_review(self):
        self.runtime.ci_hash_signal = Mock(return_value=dict(
            state='absent', approval_required=True,
            approval_url='https://github.com/example/project/actions/runs/2'))
        ap.process(self.runtime, self.state, pr())
        notice = next(message for key, label, message in self.runtime.messages if key == 'ci-approval')
        self.assertIn('watcher can approve', notice)
        self.assertIn('confirm', self.runtime.calls)
        self.assertIn('reviews', self.runtime.calls)

    def test_ci_hash_signal_never_bypasses_intake_confirmation_or_review(self):
        for status in ('success', 'failure', 'pending', 'absent', 'unavailable'):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                state = ap.State(Path(tmp), self.config)
                runtime = FakeRuntime()
                runtime.hash_state = status
                result = ap.process(runtime, state, pr())
                self.assertEqual(result['ci_hash']['state'], status)
                self.assertEqual(result['ci_hash']['acceptance'], 'not-evaluated')
                for required in ('intake', 'screen', 'confirm', 'reviews', 'publish'):
                    self.assertIn(required, runtime.calls)

    def test_crash_at_every_stage_resumes_without_repeating_successes(self):
        stages = ['fetch', 'intake', 'functions', 'screen', 'export', 'confirm', 'groups', 'reviews', 'publish', 'finish']
        for stage in stages:
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as tmp:
                state = ap.State(Path(tmp), self.config)
                runtime = FakeRuntime()
                runtime.crash = stage
                with self.assertRaises(OSError):
                    ap.process(runtime, state, pr())
                before = list(runtime.calls)
                runtime.crash = None
                state = ap.State(Path(tmp), self.config)
                self.assertTrue(ap.process(runtime, state, pr())['done'])
                for success in before[:-1]:
                    self.assertEqual(runtime.calls.count(success), 1)

    def test_updated_head_does_not_inherit_successes(self):
        ap.process(self.runtime, self.state, pr())
        ap.process(self.runtime, self.state, pr(head='d' * 40))
        self.assertEqual(self.runtime.calls.count('confirm'), 2)

    def test_fix_push_after_requested_changes_rechecks_every_gate(self):
        self.runtime.confirmed = dict(passed=[], failed=[dict(rva='0x1000', reason='comparison failed')])
        rejected = ap.process(self.runtime, self.state, pr())
        self.assertTrue(rejected['done'])
        self.assertEqual(self.runtime.messages[-1][1], 'needs-changes')
        self.assertNotIn('publish', self.runtime.calls)
        self.reload()
        ap.process(self.runtime, self.state, pr())
        self.assertEqual(self.runtime.calls.count('confirm'), 1)

        self.runtime.calls.clear()
        self.runtime.confirmed = dict(passed=['0x1000'], failed=[])
        fixed = ap.process(self.runtime, self.state, pr(head='d' * 40))
        self.assertTrue(fixed['done'])
        self.assertEqual(fixed['head'], 'd' * 40)
        self.assertEqual(self.runtime.calls, ['fetch', 'intake', 'functions', 'screen', 'export',
                                             'confirm', 'groups', 'reviews', 'publish', 'finish'])

    def test_updated_head_first_settles_an_enqueued_old_revision(self):
        rev = self.state.revision(pr())
        rev['enqueued'] = True
        self.state.save()
        self.assertIs(self.state.revision(pr(head='d' * 40)), rev)

    def test_out_of_scope_never_fetches(self):
        result = ap.process(self.runtime, self.state, pr(paths=('tools/tool.py',)))
        self.assertTrue(result['done'])
        self.assertEqual(self.runtime.calls, [])
        self.assertEqual(self.runtime.messages[0][1], 'needs-maintainer')

    def test_intake_and_ai_failures_never_compile(self):
        self.runtime.intake_errors = ['synthetic lint reason']
        ap.process(self.runtime, self.state, pr())
        self.assertNotIn('screen', self.runtime.calls)
        self.assertNotIn('confirm', self.runtime.calls)
        self.runtime.intake_errors, self.runtime.unsafe = [], True
        ap.process(self.runtime, self.state, pr(head='e' * 40))
        self.assertNotIn('confirm', self.runtime.calls)
        self.assertIn('suspicious compiler construct', self.runtime.messages[-1][2])

    def test_unavailable_closure_retries_then_requires_maintainer(self):
        self.runtime.unsafe = True
        self.runtime.screen_reasons = ['Compiler include closure was UNAVAILABLE']
        result = ap.process(self.runtime, self.state, pr())
        self.assertEqual(result['waiting_reason'], 'service-retry')
        self.assertNotIn('screen', result['completed'])
        self.assertFalse(result.get('done', False))
        ap.process(self.runtime, self.state, pr())
        result = ap.process(self.runtime, self.state, pr())
        self.assertEqual(result['waiting_reason'], 'needs-maintainer')
        ap.process(self.runtime, self.state, pr())
        self.assertEqual(self.runtime.calls.count('screen'), 3)
        self.assertFalse(any(m[1] == 'needs-changes' for m in self.runtime.messages))

    def test_filtered_and_raw_screen_reasons(self):
        placeholder = 'Details withheld by the publication filter; see the private intake log.'
        self.assertIn('Pinned toolchain and SDK system headers are hash-verified project inputs, not contributor content; do not inspect them, and their absence is not a reason for UNSAFE. Only flag includes that escape the repository or reach host files.', ap.SCREEN_CHECKLIST)
        for head, raw, expected in [('a', None, 'service-retry'), ('b', ['SDK headers unavailable'], 'service-retry'), ('c', ['macro obfuscation'], 'needs-changes'), ('d', [], 'service-retry')]:
            screening = dict(safe=False, reasons=[placeholder])
            if raw is not None:
                screening['raw_reasons'] = raw
            self.runtime.ai_screen = lambda fetched: screening
            result = ap.process(self.runtime, self.state, pr(head=head * 40))
            if expected == 'service-retry':
                self.assertEqual(result['waiting_reason'], expected)
            else:
                self.assertEqual(self.runtime.messages[-1][1], expected)

    def test_genuine_unsafe_still_needs_changes(self):
        self.runtime.unsafe = True
        result = ap.process(self.runtime, self.state, pr())
        self.assertTrue(result['done'])
        self.assertEqual(self.runtime.messages[-1][1], 'needs-changes')

    def test_function_limit_posts_changes_and_does_not_launch_model(self):
        self.runtime.reject = True
        ap.process(self.runtime, self.state, pr())
        self.assertNotIn('screen', self.runtime.calls)
        self.assertEqual(self.runtime.messages[-1][1], 'needs-changes')

    def test_function_failures_do_not_discard_the_rest(self):
        self.runtime.confirmed = dict(passed=['0x1000'], failed=[dict(rva='0x2000', reason='comparison failed')])
        ap.process(self.runtime, self.state, pr())
        self.assertIn('publish', self.runtime.calls)
        self.assertTrue(any('0x2000' in message for _, _, message in self.runtime.messages))

    def test_no_passes_or_approvals_never_publishes(self):
        self.runtime.confirmed = dict(passed=[], failed=[])
        ap.process(self.runtime, self.state, pr())
        self.assertNotIn('reviews', self.runtime.calls)
        self.runtime.confirmed = dict(passed=['0x1000'], failed=[])
        self.runtime.reviewed = dict(groups=[], failed=[dict(rva='0x1000', reason='blocking provenance')])
        ap.process(self.runtime, self.state, pr(head='e' * 40))
        self.assertNotIn('publish', self.runtime.calls)

    def test_caps_are_durable_and_roll_over_in_utc(self):
        self.state.reserve('compiles', 2)
        self.reload()
        with self.assertRaises(ap.Limit):
            self.state.reserve('compiles', 2)
        self.state.reserve('reviews', 2)
        with self.assertRaises(ap.Limit):
            self.state.reserve('reviews')
        tomorrow = ap.State(self.directory, self.config, '2026-01-02')
        tomorrow.reserve('compiles', 2)
        self.assertEqual(tomorrow.data['days']['2026-01-01']['compiles'], 2)

    def test_failed_operations_are_charged_and_not_checkpointed(self):
        revision = self.state.revision(pr())
        def operation():
            self.state.reserve('compiles', 2)
            raise OSError('crash')
        with self.assertRaises(OSError):
            self.state.once(revision, 'compile', operation)
        self.reload()
        with self.assertRaises(ap.Limit):
            self.state.once(self.state.revision(pr()), 'compile', operation)
        self.assertNotIn('compile', self.state.revision(pr())['completed'])

    def test_dry_run_completion_is_separate_from_live_state(self):
        ap.process(self.runtime, self.state, pr(), dry_run=True)
        ap.process(self.runtime, self.state, pr(), dry_run=False)
        self.assertEqual(self.runtime.calls.count('confirm'), 2)
        self.assertEqual(set(self.state.data['prs']), {'1', 'dry-1'})

    def test_lock_excludes_a_second_process(self):
        with ap.job_lock(self.directory):
            script = ('import sys;sys.path.insert(0,"tools");from pathlib import Path;'
                      'from contrib_autopilot import job_lock;\n'
                      'with job_lock(Path(sys.argv[1])): pass\n')
            proc = subprocess.run([sys.executable, '-c', script, str(self.directory)], cwd=ROOT,
                                  capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn('another run-once', proc.stderr)
        with ap.job_lock(self.directory):
            pass


class PublicationAndScheduling(unittest.TestCase):
    def test_publication_filter_does_not_echo_private_material(self):
        for value in ('private /Users/synthetic/game', 'mov qword ptr [rax], rbx', '00 11 22 33',
                      'secret\nsecond line', 'a' * 400, 'code { body }'):
            self.assertIn('withheld', ap.safe_reason(value))
        self.assertEqual(ap.safe_reason('0x1234: comparison failed'), '0x1234: comparison failed')

    def test_outside_verifiers_override_a_pc_profile_without_changing_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            config = dict(attempt='pc', confirm=['pc', 'wine'], hosts=dict(
                pc=dict(backend='ssh', loader='native', available=False),
                wine=dict(backend='local', loader='wine', host_id='mac-wine')))
            path = tree / '.local/verifier/runners.json'
            ap.save_json(path, config)
            before = path.read_bytes()
            runtime = ap.Runtime.__new__(ap.Runtime)
            runtime.root, runtime.logs = tree, tree / 'logs'
            runtime.logs.mkdir()
            runtime.config = dict(ap.DEFAULTS)
            with patch.dict(os.environ, SR_RUNNERS_CONFIG='unavailable-pc.json'), \
                    patch.object(ap.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, b'', b'')) as run:
                runtime.command([sys.executable, 'tools/verifier/confirm', 'synthetic-task'], cwd=tree)
            selected = ap.read_json(run.call_args.kwargs['env']['SR_RUNNERS_CONFIG'])
            self.assertEqual(selected['attempt'], 'wine')
            self.assertEqual(selected['confirm'], ['wine', 'ci'])
            self.assertEqual(set(selected['hosts']), {'wine', 'ci'})
            self.assertEqual(selected['hosts']['ci']['backend'], 'ci-hash')
            self.assertEqual(path.read_bytes(), before)

    def test_pc_selection_and_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            pc = dict(backend='ssh', loader='native', ssh_host='synthetic', ssh_config='config')
            wine = dict(backend='local', loader='wine')
            ap.save_json(tree / '.local/verifier/runners.json', dict(hosts=dict(pc=pc, wine=wine)))
            for reachable, expected in ((True, 'pc'), (False, 'wine')):
                runtime = ap.Runtime.__new__(ap.Runtime)
                runtime.pc_reachable = Mock(return_value=reachable)
                selected = ap.read_json(runtime.intake_runners(tree))
                self.assertEqual(selected['attempt'], expected)
                self.assertEqual(selected['confirm'], [expected, 'ci'])
                runtime.pc_reachable.assert_called_once_with(pc, tree)

    def test_pc_probe_timeout_falls_back(self):
        runtime = ap.Runtime.__new__(ap.Runtime)
        with patch.object(ap.subprocess, 'run', side_effect=subprocess.TimeoutExpired('ssh', 5)) as run:
            self.assertFalse(runtime.pc_reachable(dict(ssh_host='synthetic', ssh_config='config'), Path('.')))
        self.assertEqual(run.call_args.kwargs['timeout'], 5)

    def test_retention_protects_open_head_and_inflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = ap.Runtime.__new__(ap.Runtime)
            runtime.private, runtime.dry_run = root, False
            runtime.state = ap.State(root, ap.DEFAULTS)
            old, current, other = 'a' * 40, 'b' * 40, 'c' * 40
            for head in (old, current, other):
                (root / 'live' / ('pr-1-' + head)).mkdir(parents=True)
            runtime.state.data['prs']['1'] = dict(head=old, enqueued=True)
            runtime.prune_live(dict(number=1, headRefOid=current, state='OPEN'))
            self.assertTrue((root / 'live' / ('pr-1-' + old)).exists())
            self.assertTrue((root / 'live' / ('pr-1-' + current)).exists())
            self.assertFalse((root / 'live' / ('pr-1-' + other)).exists())
            runtime.state.data['prs']['1'].update(head=current, done=True)
            runtime.prune_live(dict(number=1, headRefOid=current, state='CLOSED'))
            self.assertEqual(list((root / 'live').iterdir()), [])
            self.assertTrue(runtime.state.data['prs']['1']['done'])

    def test_unavailable_wine_host_stops_without_pc_wake_or_fallback(self):
        runtime = ap.Runtime.__new__(ap.Runtime)
        runtime.config = dict(ap.DEFAULTS)
        runtime.command = Mock(return_value=Mock(returncode=1))
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            ap.save_json(tree / '.local/verifier/runners.json',
                         dict(hosts=dict(wine=dict(backend='local', loader='wine'))))
            with self.assertRaisesRegex(ap.Stop, 'selected first host'):
                runtime.ensure_hosts(tree)
        self.assertEqual(len(runtime.command.call_args_list), 1)

    def test_missing_wine_host_never_selects_a_native_pc(self):
        runtime = ap.Runtime.__new__(ap.Runtime)
        runtime.command = Mock()
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            ap.save_json(tree / '.local/verifier/runners.json',
                         dict(hosts=dict(pc=dict(backend='ssh', loader='native'))))
            with self.assertRaisesRegex(ap.Stop, 'project Wine host'):
                runtime.ensure_hosts(tree)
        runtime.command.assert_not_called()

    def test_preflight_uses_real_status_logic_for_wine_only(self):
        import runners
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp)
            wine = dict(backend='local', loader='wine', host_id='mac-wine', machine='synthetic-wine',
                        msvc='toolchain', work='work', wine_bin='wine', image='private-image')
            ap.save_json(tree / '.local/verifier/runners.json',
                         dict(hosts=dict(wine=wine, pc=dict(backend='ssh', available=False))))
            runtime = ap.Runtime.__new__(ap.Runtime)
            seen = []
            def command(argv, **kwargs):
                config = runners.validate(ap.read_json(kwargs['runner_config']), root=tree)
                self.assertEqual(set(config['hosts']), {'wine'})
                def probe(host):
                    seen.append(host['host_id'])
                    return dict(toolchain='ok', image='ok', loader='wine', os='macos', python='3.13',
                                cpus=1, running=0)
                with patch.object(runners, 'slots_busy', return_value=0):
                    code = runners.status(config, log=lambda line: None, probe_fn=probe)
                return subprocess.CompletedProcess(argv, code, b'', b'')
            runtime.command = command
            runtime.ensure_hosts(tree)
            self.assertEqual(seen, ['mac-wine'])

    def test_fork_ci_approval_is_reported_for_the_exact_head(self):
        runtime = ap.Runtime.__new__(ap.Runtime)
        runtime.command = Mock(side_effect=[
            subprocess.CompletedProcess([], 0, b'[{"check_runs": []}]', b''),
            subprocess.CompletedProcess([], 0, json.dumps([dict(workflow_runs=[
                dict(id=1, head_sha='b' * 40, status='action_required', html_url='https://github.com/wrong'),
                dict(id=2, head_sha='a' * 40, status='completed', conclusion='action_required',
                     html_url='https://github.com/example/project/actions/runs/2')])]).encode(), b'')])
        signal = runtime.ci_hash_signal('a' * 40)
        self.assertTrue(signal['approval_required'])
        self.assertTrue(signal['approval_url'].endswith('/2'))
        self.assertEqual(signal['acceptance'], 'not-evaluated')

    def test_real_confirmation_submission_pushes_only_an_isolated_ci_ref(self):
        import ci_confirm
        import ci_confirmation
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            name = 'reconstruction/synth/Synth.cpp'
            source = root / name
            source.parent.mkdir(parents=True)
            source.write_text('// Original synthetic submission.\n')
            request = dict(base_sha='a' * 40, files={name: ci_confirmation.sha(source.read_bytes())}, units=[])
            def command(argv, *args, **kwargs):
                if argv[:2] == ['git', 'ls-remote']:
                    return request['base_sha'] + '\trefs/heads/main'
                return 'b' * 40
            with patch.object(ci_confirm, 'command', side_effect=command) as transport, \
                    patch.object(ci_confirm, 'gh') as api:
                ci_confirm.submit(root, request, root, lambda message: None)
            pushes = [call.args[0] for call in transport.call_args_list if call.args[0][:2] == ['git', 'push']]
            self.assertEqual(len(pushes), 1)
            self.assertIn(':refs/heads/ci-confirm/', pushes[0][-1])
            self.assertNotIn(':refs/heads/main', pushes[0][-1])
            self.assertTrue(api.call_args.args[1].endswith('/dispatches'))

    def test_compiler_timeout_kills_child_and_does_not_leave_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(unit_build.UnitError) as cm:
                unit_build.compile_bounded([sys.executable, '-c',
                    'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"]);time.sleep(30)'],
                    tmp, dict(os.environ), timeout=0.1)
            self.assertEqual(cm.exception.code, 3)
            self.assertEqual(cm.exception.status, 'compile-timeout')
            self.assertFalse(any(p.is_file() for p in Path(tmp).rglob('*')))


class GitTransport(unittest.TestCase):
    """Real local git PR refs: attacker trees are never checked out or executed."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'repo'
        self.root.mkdir()
        self.git('init', '--quiet', '-b', 'main')
        self.git('config', 'user.name', 'Synthetic Maintainer')
        self.git('config', 'user.email', 'maintainer@example.invalid')
        self.origin = Path(self.tmp.name) / 'origin.git'
        subprocess.run(['git', 'init', '--quiet', '--bare', str(self.origin)], check=True)
        (self.root / '.gitignore').write_text('.local/\n')
        (self.root / 'trusted.txt').write_text('trusted\n')
        self.git('add', '.gitignore', 'trusted.txt')
        self.git('commit', '--quiet', '-m', 'base')
        self.git('remote', 'add', 'origin', str(self.origin))
        self.git('push', '--quiet', 'origin', 'main')
        self.base = self.git('rev-parse', 'HEAD')
        self.private = self.root / '.local/contrib-autopilot'
        self.private.mkdir(parents=True)
        (self.root / '.local/verifier').mkdir()
        self.state = ap.State(self.private, ap.DEFAULTS)
        self.runtime = ap.Runtime(self.root, self.private, ap.DEFAULTS, self.state)
        self.git('checkout', '--quiet', '-b', 'contributor')
        self.git('config', 'user.name', 'Original Contributor')
        self.git('config', 'user.email', 'contributor@example.invalid')
        unit = self.root / 'reconstruction/synth/Synth.cpp'
        unit.parent.mkdir(parents=True)
        unit.write_text('// Original synthetic source\nint value;\n')
        self.git('add', 'reconstruction/synth/Synth.cpp')
        self.git('commit', '--quiet', '-m', 'contribute original source')
        self.head = self.git('rev-parse', 'HEAD')
        self.git('push', '--quiet', 'origin', 'HEAD:refs/pull/1/head')
        self.git('checkout', '--quiet', 'main')

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True,
                              capture_output=True, text=True).stdout.strip()

    def _history_pr(self, message, *, extra=0, name=None):
        self.git('checkout', '--quiet', 'contributor')
        for i in range(extra):
            self.git('commit', '--quiet', '--allow-empty', '-m', f'filler {i}')
        env = dict(os.environ)
        if name:
            env['GIT_AUTHOR_NAME'] = name
        unit = self.root / 'reconstruction/synth/Synth.cpp'
        unit.write_text(unit.read_text() + '// more\n')
        self.git('add', str(unit))
        subprocess.run(['git', 'commit', '--quiet', '-m', message], cwd=self.root, check=True, env=env)
        head = self.git('rev-parse', 'HEAD')
        self.git('checkout', '--quiet', 'main')
        return head

    def test_clean_history_passes_and_is_framed_as_untrusted(self):
        from contrib_publication import screen_publication
        head = self._history_pr('Tidy the synthetic unit\n\nNo behaviour change.')
        result = screen_publication(self.root, self.base, head, merge_method='merge')
        self.assertIn('UNTRUSTED DATA', result['history'])
        self.assertIn('Tidy the synthetic unit', result['history'])
        self.assertIn('Original Contributor <contributor@example.invalid>', result['history'])
        self.assertIn('contribute original source', result['history'])

    def test_malicious_history_text_blocks_the_merge(self):
        from contrib_publication import PublicationRejected, screen_publication
        for kind, message, name in [
                ('private', 'see // PRIVATE DECOMPILER HINT: x\n\n// PRIVATE DECOMPILER HINT: y', None),
                ('path', 'copied from C:\\Users\\me\\dump', None),
                ('unixpath', 'notes in /Users/me/.local/x', None),
                ('bytes', ' '.join(['4D 5A'] * 20), None),
                ('control', 'bad\x1b[2Jtext', None),
                ('name', 'fine', 'Evil ../../.local/x')]:
            with self.subTest(kind=kind):
                head = self._history_pr(message, name=name)
                with self.assertRaises(PublicationRejected) as caught:
                    screen_publication(self.root, self.base, head, merge_method='merge')
                self.assertTrue(str(caught.exception).startswith('deterministic screen'))
                self.assertEqual(caught.exception.commit, head)
                self.assertNotIn(message, str(caught.exception))
                self.git('branch', '-f', 'contributor', self.head)

    def test_history_size_caps_are_enforced(self):
        from contrib_publication import PublicationRejected, screen_publication
        from contrib_screen import MAX_HISTORY_BYTES, MAX_MESSAGE_BYTES
        head = self._history_pr('x ' * (MAX_MESSAGE_BYTES // 2 + 1))
        with self.assertRaisesRegex(PublicationRejected, 'text-size-cap'):
            screen_publication(self.root, self.base, head, merge_method='merge')
        self.git('branch', '-f', 'contributor', self.head)
        # Each message is under its cap but the sum is over the total cap.
        self.git('checkout', '--quiet', 'contributor')
        for i in range(MAX_HISTORY_BYTES // 3000 + 2):
            self.git('commit', '--quiet', '--allow-empty', '-m', f'part {i}\n' + 'word ' * 590)
        unit = self.root / 'reconstruction/synth/Synth.cpp'
        unit.write_text(unit.read_text() + '// more\n')
        self.git('add', str(unit))
        self.git('commit', '--quiet', '-m', 'last')
        head = self.git('rev-parse', 'HEAD')
        self.git('checkout', '--quiet', 'main')
        with self.assertRaisesRegex(PublicationRejected, 'history-size-cap'):
            screen_publication(self.root, self.base, head, merge_method='merge')

    def test_squash_ignores_history_text_but_ai_screen_still_gets_it(self):
        from contrib_publication import history_report, screen_publication
        head = self._history_pr('see C:\\Users\\me\\dump')
        result = screen_publication(self.root, self.base, head)
        self.assertEqual(result['history'], '')
        from contrib_publication import PublicationRejected
        with self.assertRaises(PublicationRejected):
            history_report(self.base, head, lambda *a: subprocess.run(
                ['git', *a], cwd=self.root, check=True, capture_output=True).stdout)

    def test_ai_screen_prompt_includes_history(self):
        tree = self.private / 'live' / 'pr-1-x' / 'tree'
        tree.mkdir(parents=True)
        (tree.parent / 'diff.txt').write_text('DIFFBODY')
        (tree.parent / 'history.txt').write_text('HISTORYBODY')
        seen = []
        with patch.object(self.runtime, 'model', side_effect=lambda t, m, prompt, out: seen.append(prompt) or 'SAFE\nok'):
            result = self.runtime.ai_screen(dict(tree=str(tree), diff=str(tree.parent / 'diff.txt'),
                                                 history=str(tree.parent / 'history.txt'), merge_method='squash'))
        self.assertTrue(result['safe'])
        self.assertIn('DIFFBODY', seen[0])
        self.assertIn('HISTORYBODY', seen[0])

    def test_stale_intake_is_archived_and_checkpoints_cleared(self):
        directory = self.private / 'live' / ('pr-1-' + self.head + '-squash')
        tree = directory / 'tree'
        (tree / '.local').mkdir(parents=True)
        ap.save_json(tree / '.local/contrib-initialized.json', dict(base='a' * 40))
        (directory / 'evidence').write_text('retained')
        revision = dict(completed={key: True for key in
                        ('fetch', 'intake', 'functions', 'export', 'bind-x', 'companions',
                         'screen', 'confirm-x', 'confirmation', 'feedback-x')},
                        ci_hash={'state': 'pending'})
        self.assertTrue(self.runtime.rebase_retry(dict(tree=str(tree)), revision))
        archive = self.private / 'archive' / ('pr-1-' + self.head + '-' + 'a' * 12)
        self.assertEqual((archive / 'evidence').read_text(), 'retained')
        self.assertFalse(directory.exists())
        self.assertEqual(revision['completed'], {'feedback-x': True})
        self.assertEqual(revision['ci_hash'], {'state': 'pending'})
        self.assertEqual(revision['waiting_reason'], 'service-retry')

    def test_archive_copy_platform_flags(self):
        for platform, flags in [('darwin', ['-c', '-R']), ('linux', ['-R'])]:
            directory = self.private / 'live' / ('pr-1-' + self.head + '-squash')
            tree = directory / 'tree'
            (tree / '.local').mkdir(parents=True)
            ap.save_json(tree / '.local/contrib-initialized.json', dict(base='a' * 40))
            revision = dict(completed={})
            with patch.object(ap.sys, 'platform', platform), patch.object(self.runtime, 'command') as command:
                self.runtime.rebase_retry(dict(tree=str(tree)), revision)
            copy = next(call.args[0] for call in command.call_args_list if call.args[0][0] == 'cp')
            self.assertEqual(copy[1:-2], flags)

    def test_enqueued_intake_is_untouched(self):
        revision = dict(enqueued=True, completed={'fetch': True})
        with patch.object(self.runtime, 'git') as git:
            self.assertFalse(self.runtime.rebase_retry(dict(tree='unused'), revision, force=True))
        git.assert_not_called()
        self.assertEqual(revision['completed'], {'fetch': True})

    def test_rerun_uses_live_origin_main_in_new_clean_tree(self):
        import flow
        tree = self.root / 'frozen'
        tree.mkdir()
        (self.root / 'trusted.txt').write_text('new main\n')
        self.git('add', 'trusted.txt')
        self.git('commit', '--quiet', '-m', 'advance main')
        self.git('push', '--quiet', 'origin', 'main')
        live = self.git('rev-parse', 'HEAD')
        self.assertNotEqual(live, self.base)
        clean = tree.parent / ('rerun-g1-' + live[:12])
        with patch.object(self.runtime, 'link_inputs'), \
             patch.object(flow, 'inventory', return_value={'functions': []}), \
             patch.object(flow, 'record_rerun', return_value=(True, [])):
            self.runtime.rerun({'tree': str(tree), 'base': self.base},
                               {'name': 'g1', 'sampled': [], 'build_id': 'synthetic'}, [], {})
        for ref in ('HEAD', 'refs/remotes/origin/main'):
            actual = subprocess.check_output(['git', 'rev-parse', ref], cwd=clean, text=True).strip()
            self.assertEqual(actual, live)

    def test_fetch_materializes_only_blobs_on_trusted_main(self):
        fetched = self.runtime.fetch(pr(head=self.head))
        self.assertNotIn('problem', fetched)
        tree = Path(fetched['tree'])
        self.assertEqual(self.runtime.git(tree, 'rev-parse', 'HEAD'), self.base)
        self.assertEqual((tree / 'trusted.txt').read_text(), 'trusted\n')
        self.assertEqual((tree / 'reconstruction/synth/Synth.cpp').read_text(), '// Original synthetic source\nint value;\n')
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.base)

    def test_unsafe_tip_and_historical_out_of_scope_are_refused(self):
        self.git('checkout', '--quiet', 'contributor')
        (self.root / 'reconstruction/synth/Synth.cpp').write_text('#pragma comment(lib,"malicious")\n')
        self.git('add', 'reconstruction/synth/Synth.cpp')
        self.git('commit', '--quiet', '-m', 'bad compiler input')
        bad = self.git('rev-parse', 'HEAD')
        self.git('push', '--quiet', '--force', 'origin', 'HEAD:refs/pull/1/head')
        self.git('checkout', '--quiet', 'main')
        self.assertIn('deterministic screen', self.runtime.fetch(pr(head=bad))['problem'])
        self.git('checkout', '--quiet', 'contributor')
        self.git('reset', '--hard', self.head)
        (self.root / 'trusted.txt').write_text('attacker history\n')
        self.git('add', 'trusted.txt')
        self.git('commit', '--quiet', '-m', 'hidden tool change')
        (self.root / 'trusted.txt').write_text('trusted\n')
        self.git('add', 'trusted.txt')
        self.git('commit', '--quiet', '-m', 'hide change from tip diff')
        hidden = self.git('rev-parse', 'HEAD')
        self.git('push', '--quiet', '--force', 'origin', 'HEAD:refs/pull/1/head')
        self.git('checkout', '--quiet', 'main')
        self.runtime.config = dict(self.runtime.config, merge_method='merge')
        self.assertIn('history changes files outside', self.runtime.fetch(pr(head=hidden))['problem'])

    def test_fixed_tip_squashes_without_rejected_ancestor_and_keeps_credit(self):
        import flow_lane
        self.git('checkout', '--quiet', 'contributor')
        source = self.root / 'reconstruction/synth/Synth.cpp'
        source.write_text('#include "../synth/Private.h"\n')
        self.git('add', 'reconstruction/synth/Synth.cpp')
        self.git('commit', '--quiet', '-m', 'rejected include')
        bad = self.git('rev-parse', 'HEAD')
        source.write_text('// Original synthetic source\nint value;\n')
        self.git('add', 'reconstruction/synth/Synth.cpp')
        self.git('commit', '--quiet', '-m', 'fix include at tip')
        fixed = self.git('rev-parse', 'HEAD')
        self.git('push', '--quiet', 'origin', 'HEAD:refs/pull/1/head')
        self.git('checkout', '--quiet', 'main')
        fetched = self.runtime.fetch(pr(head=fixed))
        self.assertNotIn('problem', fetched)
        self.assertEqual(fetched['merge_method'], 'squash')
        self.assertNotIn('../synth/Private.h', Path(fetched['diff']).read_text())
        contribution = dict(self.contribution(), head=fixed, merge_method='squash')
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text('// Original synthetic source\nint value;\n')
        self.git('add', 'reconstruction/synth/Synth.cpp')
        flow_lane.commit_acceptance(self.root, [dict(item='item', contributor=contribution)],
            [dict(id='item', root=str(self.root))], 'Accept synthetic squash', '2026-01-01T00:00:00+00:00')
        self.assertEqual(self.git('rev-list', '--parents', '-n', '1', 'HEAD').split()[1:], [self.base])
        self.assertNotIn(bad, self.git('rev-list', 'HEAD').splitlines())
        self.assertNotIn(fixed, self.git('rev-list', 'HEAD').splitlines())
        self.assertIn('Co-authored-by: Original Contributor <contributor@example.invalid>',
                      self.git('log', '-1', '--format=%B'))
        self.assertEqual(self.git('rev-parse', 'contributor'), fixed)
        # Retaining this same history still refuses the original bad include.
        with self.assertRaisesRegex(Exception, 'deterministic screen'):
            flow_lane.contributor_history(self.root, self.root, dict(contribution, merge_method='merge'))
        from contrib_publication import PublicationRejected, screen_publication
        with self.assertRaises(PublicationRejected) as caught:
            screen_publication(self.root, self.base, fixed, merge_method='merge')
        self.assertEqual(caught.exception.commit, bad)
        self.assertEqual(caught.exception.path, 'reconstruction/synth/Synth.cpp')

    def test_shared_screen_refusals_identify_commit_and_path_without_echoing_them(self):
        from contrib_publication import PublicationRejected, screen_publication
        for kind, content in [('screen', '#pragma comment(lib,"malicious")\n'),
                              ('size', 'x' * (screen.MAX_BYTES + 1)),
                              ('mode', 'synthetic-link-target\n')]:
            with self.subTest(kind=kind):
                self.git('checkout', '--quiet', 'contributor')
                name = 'reconstruction/synth/Synth.cpp'
                (self.root / name).write_text(content)
                self.git('add', name)
                if kind == 'mode':
                    blob = self.git('rev-parse', ':' + name)
                    self.git('update-index', '--cacheinfo', '120000,' + blob + ',' + name)
                self.git('commit', '--quiet', '-m', 'synthetic refusal ' + kind)
                bad = self.git('rev-parse', 'HEAD')
                if kind == 'mode':
                    self.git('reset', '--hard', 'HEAD')  # Materialize the synthetic index-only symlink.
                self.git('checkout', '--quiet', 'main')
                with self.assertRaises(PublicationRejected) as caught:
                    screen_publication(self.root, self.base, bad)
                self.assertEqual(caught.exception.commit, bad)
                self.assertEqual(caught.exception.path, name)
                self.assertNotIn(bad, str(caught.exception))
                self.assertNotIn(name, str(caught.exception))

    def contribution(self):
        return dict(head=self.head, base=self.base, authors=['Original Contributor <contributor@example.invalid>'],
                    paths=['reconstruction/synth/Synth.cpp'])

    def test_lane_merge_keeps_original_parent_and_exact_author_trailer(self):
        import flow_lane
        # Only the accepted data is in the index. PR source is not implicitly merged.
        (self.root / 'accepted.txt').write_text('accepted synthetic result\n')
        self.git('add', 'accepted.txt')
        request = dict(item='synthetic-item', contributor=self.contribution())
        flow_lane.commit_acceptance(self.root, [request], [dict(id='synthetic-item', root=str(self.root))],
                                    'Accept synthetic contribution', '2026-01-01T00:00:00+00:00')
        parents = self.git('rev-list', '--parents', '-n', '1', 'HEAD').split()[1:]
        self.assertEqual(parents, [self.base, self.head])
        self.assertEqual(self.git('show', self.head + ':reconstruction/synth/Synth.cpp'), '// Original synthetic source\nint value;')
        self.assertFalse((self.root / 'reconstruction/synth/Synth.cpp').exists())
        self.assertIn('Co-authored-by: Original Contributor <contributor@example.invalid>', self.git('log', '-1', '--format=%B'))
        self.assertEqual(self.git('log', '-1', '--format=%an <%ae>', self.head),
                         'Original Contributor <contributor@example.invalid>')
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_lane_refuses_forged_authorship_or_paths(self):
        import flow_lane
        for field, value in [('authors', ['Someone Else <someone@example.invalid>']), ('paths', ['tools/tool.py'])]:
            contribution = dict(self.contribution(), **{field: value})
            with self.subTest(field=field), self.assertRaises(Exception):
                flow_lane.contributor_history(self.root, self.root, contribution)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.base)


class RuntimeEffects(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.private = self.root / '.local/contrib-autopilot'
        self.private.mkdir(parents=True)
        self.state = ap.State(self.private, ap.DEFAULTS)
        with patch.object(ap, 'shared_root', return_value=self.root):
            self.runtime = ap.Runtime(self.root, self.private, ap.DEFAULTS, self.state)

    def test_dry_feedback_has_no_external_write_and_keeps_commit_sha(self):
        self.runtime.dry_run = True
        rev = self.state.revision(pr(), True)
        with patch.object(self.runtime, 'command', side_effect=AssertionError('no GitHub mutation')):
            self.runtime.feedback(rev, 'test', 'needs-changes', 'unsafe /Users/synthetic/file', commits=['c' * 40])
        body = rev['would_post']['test']['body']
        self.assertNotIn('/Users/', body)
        self.assertIn('c' * 40, body)

    def test_comment_recovery_finds_marker_before_posting_again(self):
        rev = self.state.revision(pr())
        marker = f'<!-- contrib-autopilot:1:{rev["head"]}:test -->'
        result = subprocess.CompletedProcess([], 0, json.dumps([[dict(body=marker, user=dict(login='awarebayes'))]]).encode(), b'')
        with patch.object(self.runtime, 'command', return_value=result), patch.object(self.runtime, 'gh') as gh:
            self.runtime.feedback(rev, 'test', 'needs-changes', 'synthetic reason')
        self.assertFalse(any(call.args[:2] == ('pr', 'comment') for call in gh.call_args_list))
        self.assertTrue(any(call.args[:2] == ('pr', 'edit') for call in gh.call_args_list))

    def test_final_feedback_updates_existing_comment_after_saved_checkpoint(self):
        rev = self.state.revision(pr())
        rev['completed']['post-published'] = True
        marker = f'<!-- contrib-autopilot:1:{"d" * 40}:feedback -->'
        result = subprocess.CompletedProcess([], 0, json.dumps([[dict(id=42, body=marker + '\nold totals',
                    user=dict(login='awarebayes'))]]).encode(), b'')
        with patch.object(self.runtime, 'command', return_value=result) as command, patch.object(self.runtime, 'gh') as gh:
            self.runtime.feedback(rev, 'published', None, 'Submitted functions: 2.', replace=True)
        self.assertEqual(command.call_count, 2)
        self.assertIn('PATCH', command.call_args.args[0])
        self.assertIn('repos/awarebayes/skyrim_decomp/issues/comments/42', command.call_args.args[0])
        gh.assert_not_called()

    def test_plural_rvas_discover_every_member(self):
        cpp = 'reconstruction/synth/Synth.cpp'
        unit = self.root / cpp
        unit.parent.mkdir(parents=True)
        unit.write_text('// RVAs 0x1000, 0x2000, and 0x3000, 3 bytes each.\n// RVA 0x1000\nint Synthetic() { return 0; }\n')
        ap.save_json(self.root / 'data/progress.json', dict(target_build_id='synthetic', functions=[
            dict(build_id='synthetic', rva=r, status='mapped') for r in (0x1000, 0x2000, 0x3000)]))
        with patch.object(ap, 'screen_tree', return_value=[]):
            self.assertEqual(self.runtime.functions(dict(tree=str(self.root), files=[dict(path=cpp)])),
                             {cpp: [0x1000, 0x2000, 0x3000]})

    def test_header_rva_accepted_in_another_unit_is_not_a_regression_target(self):
        cpp = 'reconstruction/synth/Synth.cpp'
        unit = self.root / cpp
        unit.parent.mkdir(parents=True)
        unit.write_text('// RVA 0x1000; RVA 0x2000; RVA 0x3000.\nint Synthetic() { return 0; }\n')
        for name, compiled in (('0x2000', cpp), ('0x3000', 'reconstruction/synth_other/Synth.cpp')):
            ap.save_json(self.root / 'reports' / (name + '.json'), dict(source=dict(compiled=compiled, translation_unit=[compiled])))
        ap.save_json(self.root / 'data/progress.json', dict(target_build_id='synthetic', functions=[
            dict(build_id='synthetic', rva=0x1000, status='mapped'),
            dict(build_id='synthetic', rva=0x2000, status='matched', report='reports/0x2000.json'),
            dict(build_id='synthetic', rva=0x3000, status='matched', report='reports/0x3000.json')]))
        with patch.object(ap, 'screen_tree', return_value=[]):
            self.assertEqual(self.runtime.functions(dict(tree=str(self.root), files=[dict(path=cpp)])),
                             {cpp: [0x1000, 0x2000]})

    def test_finish_accounts_for_preintegration_failures_and_missing_members(self):
        rev = self.state.revision(pr())
        rev['completed']['functions'] = {'synthetic.cpp': [0x1000, 0x2000, 0x3000]}
        rev['completed']['confirmation'] = dict(failed=[dict(rva='0x2000', reason='two-host confirmation failed')])
        published = dict(accepted=['0x1000'], dropped=0, failures=[], commits=['c' * 40])
        with patch.object(self.runtime, 'feedback') as feedback, \
             patch.object(self.runtime, 'gh', return_value=subprocess.CompletedProcess([], 0, b'{"labels":[]}', b'')), \
             patch.object(self.runtime, 'current_head', return_value='b' * 40):
            self.runtime.finish(rev, published)
        message = feedback.call_args.args[3]
        self.assertIn('Submitted functions: 3.', message)
        self.assertIn('0x2000: two-host confirmation failed', message)
        self.assertIn('0x3000: not accepted; intake processing incomplete.', message)
        self.assertIn('Functions not accepted: 2.', message)
        self.assertEqual(feedback.call_args.args[2], 'needs-changes')

    def test_finish_expands_group_only_review_failure_to_members(self):
        rev = self.state.revision(pr())
        rev['completed']['functions'] = {'synthetic.cpp': [0x1000]}
        rev['completed']['reviews'] = dict(failed=[dict(group='held', reason='sampling disagreement; batch paused')])
        ap.save_json(self.runtime.fdir / 'groups/held.json', dict(functions=['0x1000']))
        with patch.object(self.runtime, 'feedback') as feedback, \
             patch.object(self.runtime, 'gh', return_value=subprocess.CompletedProcess([], 0, b'{"labels":[]}', b'')):
            self.runtime.finish(rev, dict(accepted=[], dropped=0, failures=[], commits=[]))
        self.assertIn('0x1000: sampling disagreement; batch paused', feedback.call_args.args[3])
        self.assertEqual(feedback.call_args.args[2], 'needs-changes')

    def test_finish_removes_stale_label_after_full_acceptance(self):
        rev = self.state.revision(pr())
        rev['completed']['functions'] = {'synthetic.cpp': [0x1000]}
        result = subprocess.CompletedProcess([], 0, b'{"labels":[{"name":"needs-changes"}]}', b'')
        with patch.object(self.runtime, 'feedback') as feedback, patch.object(self.runtime, 'gh', return_value=result) as gh, \
             patch.object(self.runtime, 'current_head', return_value='b' * 40):
            self.runtime.finish(rev, dict(accepted=['0x1000'], dropped=0, failures=[], commits=[]))
        self.assertIsNone(feedback.call_args.args[2])
        self.assertTrue(any(c.args[-2:] == ('--remove-label', 'needs-changes') for c in gh.call_args_list))

    def _merge_fixture(self, head_after='a' * 40, screen_error=None, push_codes=(0,)):
        rev = self.state.revision(pr(number=7, author='someone'))
        rev['completed']['functions'] = {'synthetic.cpp': [0x1000]}
        calls = []
        pushes = list(push_codes)

        def command(argv, cwd=None, **kw):
            calls.append([str(a) for a in argv])
            out = b''
            if argv[:2] == ['git', 'rev-parse']:
                out = b'a' * 40 if argv[2] == 'FETCH_HEAD' else b'f' * 40
            elif argv[:2] == ['git', 'log']:
                out = b'them@example.invalid'
            code = pushes.pop(0) if argv[:2] == ['git', 'push'] else 0
            return subprocess.CompletedProcess(argv, code, out, b'')

        def gh(*args):
            calls.append(['gh', *args])
            body = b'{"state":"OPEN"}' if 'state' in args else b'{"labels":[]}'
            return subprocess.CompletedProcess([], 0, body, b'')

        import contrib_publication as cp
        screen = patch.object(cp, 'screen_publication',
                              side_effect=screen_error) if screen_error else patch.object(cp, 'screen_publication')
        stack = [patch.object(self.runtime, 'command', side_effect=command),
                 patch.object(self.runtime, 'gh', side_effect=gh),
                 patch.object(self.runtime, 'current_head', return_value=head_after), screen,
                 patch.object(self.runtime, 'feedback')]
        return rev, calls, stack

    def _run_finish(self, rev, stack):
        mocks = []
        from contextlib import ExitStack
        with ExitStack() as es:
            mocks = [es.enter_context(p) for p in stack]
            self.runtime.finish(rev, dict(accepted=['0x1000'], dropped=0, failures=[], commits=['c' * 40]))
        return mocks

    def test_accepted_pr_is_merged_with_tree_neutral_merge(self):
        rev, calls, stack = self._merge_fixture()
        screen, feedback = self._run_finish(rev, stack)[3:]
        self.assertEqual(rev['completed']['merge'], 'merged')
        self.assertEqual(screen.call_args.kwargs['merge_method'], 'merge')
        merge = next(c for c in calls if c[:2] == ['git', 'merge'])
        self.assertEqual(merge[2:5], ['-s', 'ours', '--no-ff'])
        self.assertEqual(merge[-1], 'a' * 40)
        self.assertIn('Merge contributor PR #7 from someone', merge[6])
        self.assertIn('Co-authored-by: someone <them@example.invalid>', merge[6])
        self.assertIn(['git', 'push', 'origin', 'HEAD:main'], calls)
        self.assertTrue(any(c[:3] == ['git', 'worktree', 'remove'] and '--force' not in c for c in calls))
        self.assertFalse(any(c[:3] == ['gh', 'pr', 'close'] for c in calls))
        self.assertIn('@someone', feedback.call_args.args[3])
        self.assertIn('merged', feedback.call_args.args[3])

    def test_non_fast_forward_push_retries_once(self):
        rev, calls, stack = self._merge_fixture(push_codes=(1, 0))
        self._run_finish(rev, stack)
        self.assertEqual(rev['completed']['merge'], 'merged')
        self.assertEqual(sum(c[:2] == ['git', 'merge'] for c in calls), 2)
        self.assertIn(['git', 'reset', '--hard', 'f' * 40], calls)

    def test_history_screen_failure_leaves_pr_open_without_close(self):
        import contrib_publication as cp
        rev, calls, stack = self._merge_fixture(screen_error=cp.PublicationRejected('bad history'))
        feedback = self._run_finish(rev, stack)[4]
        self.assertEqual(rev['completed']['merge'], 'history')
        self.assertFalse(any(c[:2] == ['git', 'merge'] or c[:2] == ['git', 'push'] for c in calls))
        self.assertFalse(any(c[:3] == ['gh', 'pr', 'close'] for c in calls))
        self.assertIn('stays open', feedback.call_args.args[3])

    def test_changed_head_skips_merge(self):
        rev, calls, stack = self._merge_fixture(head_after='b' * 40)
        self._run_finish(rev, stack)
        self.assertEqual(rev['completed']['merge'], 'head-changed')
        self.assertFalse(any(c[:2] == ['git', 'merge'] for c in calls))

    def test_timeout_keeps_diagnostics_in_private_log(self):
        with patch.object(ap.subprocess, 'run', side_effect=subprocess.TimeoutExpired(['synthetic'], 1, output=b'partial')):
            with self.assertRaises(subprocess.TimeoutExpired):
                self.runtime.command(['synthetic'])
        self.assertEqual(next(self.runtime.logs.glob('*.log')).read_bytes(), b'partial\n')
        self.assertEqual(self.state.data['last_timeout']['command'], ['synthetic'])

    def test_pending_publication_uses_fresh_trusted_main_tools(self):
        tree = self.root / 'frozen'
        revision = self.state.revision(pr())
        revision['enqueued'] = True
        ap.save_json(self.runtime.fdir / 'lane/queue/item.json',
                     dict(root=str(tree), selection=['g1'], state='running'))
        pending = dict(settled=False)
        green = dict(settled=True, accepted=['0x1000'])
        with patch.object(self.runtime, 'lane_result', side_effect=[pending, green]), \
             patch.object(self.runtime, 'git', return_value='b' * 40), \
             patch.object(self.runtime, 'prepare_main_tree') as prepare, \
             patch.object(self.runtime, 'command') as command:
            self.assertEqual(self.runtime.publish(dict(tree=str(tree)), dict(groups=['g1']), revision), green)
        publisher = tree.parent / ('publisher-' + 'b' * 40)
        prepare.assert_called_once_with(publisher, 'b' * 40)
        self.assertEqual(command.call_args.kwargs['cwd'], publisher)
        self.assertNotEqual(command.call_args.kwargs['cwd'], tree)

    def test_model_uses_fresh_exact_model_and_read_only_sandbox(self):
        output = self.root / 'review.md'
        def command(argv, **kwargs):
            response = Path(argv[argv.index('--output-last-message') + 1])
            response.write_text('SAFE\nsynthetic\n')
            return subprocess.CompletedProcess(argv, 0, b'', b'')
        with patch.object(self.runtime, 'command', side_effect=command) as called:
            self.runtime.model(self.root, 'gpt-6.1-sol', 'synthetic diff', output)
        argv = called.call_args.args[0]
        self.assertEqual(argv[:2], ['codex', 'exec'])
        self.assertEqual(argv[argv.index('--model') + 1], 'gpt-6.1-sol')
        self.assertEqual(argv[argv.index('--sandbox') + 1], 'read-only')
        self.assertIn('--ephemeral', argv)
        self.assertNotIn('resume', argv)
        self.assertEqual(output.read_text(), 'SAFE\nsynthetic\n')
        self.assertEqual(self.state.data['days'][self.state.today]['reviews'], 1)

    def test_model_response_path_has_no_symlink_when_output_is_in_a_symlinked_store(self):
        store = self.root / 'shared-store'
        store.mkdir()
        tree = self.root / 'tree'
        tree.mkdir()
        (tree / 'reviews').symlink_to(store, target_is_directory=True)
        output = tree / 'reviews' / 'review.md'
        seen = []
        def command(argv, **kwargs):
            response = Path(argv[argv.index('--output-last-message') + 1])
            seen.append(response)
            # codex refuses any path containing a symlink component.
            self.assertEqual(os.path.realpath(response.parent), str(response.parent))
            response.write_text('APPROVE\nsynthetic\n')
            return subprocess.CompletedProcess(argv, 0, b'', b'')
        with patch.object(self.runtime, 'command', side_effect=command):
            value = self.runtime.model(tree, 'gpt-6.1-sol', 'synthetic', output)
        self.assertEqual(value, 'APPROVE\nsynthetic\n')
        self.assertEqual((store / 'review.md').read_text(), value)
        self.assertFalse(seen[0].exists())

    def test_all_dropped_receipt_is_terminal_and_not_a_fake_acceptance(self):
        tree = self.root / 'tree'
        fdir = self.runtime.fdir
        ap.save_json(fdir / 'lane/queue/item.json', dict(id='item', root=str(tree), selection=['g1'], state='dropped', run='run1'))
        ap.save_json(fdir / 'lane/runs/run1.json', dict(state='done', integrated=None, dropped=[dict(item='item', reason='synthetic refusal')]))
        ap.save_json(fdir / 'groups/g1.json', dict(functions=['0x1000']))
        result = self.runtime.lane_result(tree, dict(groups=['g1']))
        self.assertTrue(result['settled'])
        self.assertEqual(result['accepted'], [])
        self.assertEqual(result['commits'], [])
        self.assertEqual(result['dropped'], 1)

    def test_green_receipt_after_crash_does_not_enqueue_or_push_again(self):
        tree = self.root / 'tree'
        fdir = self.runtime.fdir
        ap.save_json(fdir / 'lane/queue/item.json', dict(root=str(tree), selection=['g1'], state='done', run='run1'))
        ap.save_json(fdir / 'lane/runs/run1.json', dict(state='done', integrated=dict(ci='green', pushed='yes', commit='c' * 40),
                    accepted=[dict(group='g1', functions=['0x1000'])], dropped=[]))
        rev = self.state.revision(pr())
        rev['enqueued'] = True
        with patch.object(self.runtime, 'command', side_effect=AssertionError('must reuse green receipt')):
            result = self.runtime.publish(dict(tree=str(tree)), dict(groups=['g1']), rev)
        self.assertEqual(result['commits'], ['c' * 40])
        self.assertEqual(result['accepted'], ['0x1000'])


class SyntheticEndToEnd(unittest.TestCase):
    """Real git transport, state, review parser, sampling comparison and acceptance preparation.

    Only GitHub, model output and host/export commands are substituted. Comparator records are
    produced from the original synthetic COFF/PE fixtures, not hand-written success reports.
    """
    def setUp(self):
        import test_match_gate as fixture
        self.fixture = fixture
        self.kit = type('Kit', (fixture.GateFixture,), {'addCleanup': self.addCleanup})()
        self.kit.setUp()
        self.addCleanup(self.kit.tearDown)
        self.root = self.kit.root.resolve()
        self.kit.root = self.root
        self.kit.fn['status'] = 'mapped'
        (self.root / fixture.REVIEW).unlink()
        self.kit.write('data/progress.json', json.dumps(self.kit.data))
        self.kit.write('builds/target.json', json.dumps(self.kit.target))
        self.kit.write('docs/verification.md', (ROOT / 'docs/verification.md').read_bytes())
        self.kit.write('.gitignore', '.local/\n')
        self.kit.write('tools/trusted.txt', 'original trusted main tools\n')
        self.kit.write('tools/toolchain/v141-manifest.json', '{}')
        import ci_confirmation
        self.ci_row = dict(rva=self.kit.fn['rva'], size=self.kit.fn['size'],
                          extraction='linked-reference-inference', normalized_sha256='1' * 64,
                          layout_sha256='2' * 64)
        tools = patch.object(ci_confirmation, 'tools_digest_at', return_value='3' * 64)
        targets = patch.object(ci_confirmation.target_hashes, 'load_manifest',
                               return_value={'functions': [self.ci_row]})
        tools.start(); targets.start()
        self.addCleanup(tools.stop); self.addCleanup(targets.stop)
        self.git('init', '--quiet', '-b', 'main')
        self.git('config', 'user.name', 'Synthetic Maintainer')
        self.git('config', 'user.email', 'maintainer@example.invalid')
        self.git('add', '.gitignore', 'builds', 'data', 'docs', 'findings', 'reconstruction', 'reports', 'tools')
        self.git('commit', '--quiet', '-m', 'synthetic baseline')
        self.origin = self.root / '.local/origin.git'
        self.origin.parent.mkdir(exist_ok=True)
        self.run_git('init', '--quiet', '--bare', str(self.origin))
        self.git('remote', 'add', 'origin', str(self.origin))
        self.git('push', '--quiet', 'origin', 'main')
        self.base = self.git('rev-parse', 'HEAD')
        self.git('checkout', '--quiet', '-b', 'contributor')
        self.git('config', 'user.name', 'Original Contributor')
        self.git('config', 'user.email', 'contributor@example.invalid')
        cpp = self.root / fixture.CPP
        cpp.write_text('// RVA 0x1010, 16 bytes\n// Recipe: reconstruction/recipes/synthetic.json\n' + cpp.read_text())
        self.git('add', fixture.CPP)
        self.git('commit', '--quiet', '-m', 'original synthetic contribution')
        self.head = self.git('rev-parse', 'HEAD')
        self.git('push', '--quiet', 'origin', 'HEAD:refs/pull/1/head')
        self.git('checkout', '--quiet', 'main')
        ap.save_json(self.root / '.local/verifier/runners.json', dict(confirm=['mac', 'windows'], attempt='mac',
                     hosts={'mac': dict(backend='local', loader='wine'),
                            'windows': dict(backend='ssh', loader='native', available=False)}))
        self.private = self.root / '.local/contrib-autopilot'
        self.private.mkdir()
        self.state = ap.State(self.private, ap.DEFAULTS)
        self.runtime = ap.Runtime(self.root, self.private, ap.DEFAULTS, self.state, dry_run=True)
        self.commands, self.models = [], []
        self.real_command = self.runtime.command
        self.runtime.command = self.command
        self.runtime.model = self.model

    def run_git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True, text=True).stdout.strip()

    def git(self, *args):
        return self.run_git(*args)

    def command(self, argv, cwd=None, **kwargs):
        argv = list(map(str, argv))
        cwd = Path(cwd or self.root)
        self.commands.append(argv)
        output = b''
        if argv[0] == 'gh':
            if argv[1] == 'api':
                if '/actions/runs?' in argv[-1]:
                    return subprocess.CompletedProcess(argv, 0, b'[{"workflow_runs": []}]', b'')
                self.assertTrue(argv[-1].endswith('/check-runs'))
                return subprocess.CompletedProcess(argv, 0, b'[{"check_runs": []}]', b'')
            self.assertEqual(argv[1:3], ['pr', 'view'])
            output = json.dumps(dict(headRefOid=self.head, state='OPEN')).encode()
        elif len(argv) > 1 and argv[1] == 'tools/contrib.py':
            self.assertIn('--base', argv)
            self.assertIn('origin/main', argv)
            self.assertIn('contrib/pr-1', argv)
            output = b'{"problems": [], "ok": true}'
        elif len(argv) > 1 and argv[1] == 'tools/ghidra/export_pack.py':
            rows = Path(argv[3]).read_text().splitlines()
            for row in rows:
                build, rva, tid, cpp, recipe = row.split()
                self.assertEqual(recipe, 'recipe=synthetic')
                ap.save_json(cwd / '.local/tasks' / tid / 'task.json', dict(task_id=tid, build_id=build,
                             compiled=cpp, recipe=self.fixture.RECIPE, symbols='symbols.json',
                             functions=[dict(rva=rva, size=self.kit.fn['size'], symbol='SyntheticSum')]))
        elif len(argv) > 1 and argv[1] in ('tools/verifier/attempt', 'tools/verifier/wine_confirm.py'):
            selected = ap.read_json(self.runtime.intake_runners(cwd))
            self.assertEqual(set(selected['hosts']), {'wine', 'ci'})
        elif len(argv) > 1 and argv[1] == 'tools/verifier/bind.py':
            directory = Path(Path(argv[argv.index('--list') + 1]).read_text().strip())
            task = ap.read_json(directory / 'task.json')
            task['symbols'] = self.fixture.MAP
            ap.save_json(directory / 'task.json', task)
        elif len(argv) > 1 and argv[1] == 'tools/verifier/confirm':
            selected = ap.read_json(self.runtime.intake_runners(cwd))
            self.assertEqual(selected['hosts']['ci']['backend'], 'ci-hash')
            self.assertNotIn('windows', selected['hosts'])
            output_dir = Path(argv[argv.index('--out') + 1])
            original = self.kit.root
            try:
                self.kit.root = cwd
                self.kit.record = self.kit.make_record()
                self.kit.record['build'] = self.kit.build_block()
            finally:
                self.kit.root = original
            import ci_confirmation as ci
            record = self.kit.record
            record['runs'] = record['runs'][:1]
            record['runs'][0].update(compiled_on='mac-wine', compared_on='mac-wine')
            record['build']['hosts'] = {'mac-wine': next(iter(record['build']['hosts'].values()))}
            pins = {name: digest for digest, name in
                    (line.split() for line in (cwd / 'tools/verifier/pinned.sha256').read_text().splitlines())}
            record['ci_confirmation'] = dict(schema=1, kind='ci-hash', host_id='github-windows-native',
                machine='github-hosted-windows', loader='native', os='windows', workflow=ci.WORKFLOW,
                conclusion='success', run_id=123, run_attempt=1, base_sha=self.base, candidate_sha='b' * 40,
                tools_sha256='3' * 64, toolchain_manifest_sha256=ci.sha(b'{}'), cache_verified=True,
                toolset='MATCH', compiler_sha256=pins, target=self.ci_row, build_id=self.kit.target['build_id'],
                source_sha256=record['source']['digest'], unit=record['source']['compiled'],
                recipe_sha256=record['recipe']['sha256'], result='hash-match', deterministic=True,
                mac_content_sha256='4' * 64, content_sha256='4' * 64, object_sha256='5' * 64,
                request_sha256='6' * 64, normalized_sha256='1' * 64, layout_sha256='2' * 64,
                mac_object_sha256=record['runs'][0]['report']['candidate']['object_sha256'])
            ap.save_json(output_dir / 'synthetic-fixture/0x1010.json', record)
        elif len(argv) > 1 and argv[1] == 'tools/verifier/runners.py':
            selected = ap.read_json(self.runtime.intake_runners(cwd))
            self.assertNotIn('windows', selected['hosts'])
        else:
            return self.real_command(argv, cwd=cwd, **kwargs)
        return subprocess.CompletedProcess(argv, 0, output, b'')

    def model(self, tree, model, prompt, output):
        self.state.reserve('reviews')
        self.models.append(model)
        if output.name == 'engineer-screen.txt':
            document = 'SAFE\nOriginal synthetic programmer source.\n'
        else:
            import source_digest
            task = output.stem
            document = f'''# Review {task}

reviewer_model: {model}
fresh_context: yes
drafted_or_triaged_any_reviewed_function: no
gates_in_force: claude-low
source_revision: {self.base}
sampling_second_pass: {'yes' if task.endswith('-s') else 'no'}
decompiler_output_read: no

## synthetic-fixture 0x1010 {self.kit.fn['size']}

verdict: approve
escalation_category: none
review_kind: full
source_paths: {self.fixture.CPP} {self.fixture.HDR}
source_digest: {source_digest.tu_digest(tree, [self.fixture.CPP, self.fixture.HDR])}
report_path: {self.fixture.RECORD}
report_binding: agree, synthetic comparator reports
checks:
  plausible_source: pass, synthetic
  provenance: pass, original synthetic fixture
  claim_scope: pass, byte match only
  publication_hygiene: pass, original fixture only
blocking_findings: none
naming_findings: none
reasons: original synthetic source and comparator reports
'''
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(document)
        return document

    def test_companion_credit_survives_shared_unit_digest_change(self):
        info = pr(author='Later-Contributor', head=self.head, paths=(self.fixture.CPP,))
        revision = self.state.revision(info, True)
        fetched = self.runtime.fetch(info)
        fetched.update(number=1, head=self.head)
        tree = Path(fetched['tree'])
        path = tree / self.fixture.RECORD
        previous = ap.read_json(path)
        previous['submitter'] = 'earlier-contributor'
        previous['matchers'] = [dict(handle='earlier-contributor', model='not-reported')]
        ap.save_json(path, previous)
        tasks = self.runtime.export(fetched, self.runtime.functions(fetched))
        confirmed = self.runtime.confirm(fetched, tasks, revision)
        self.assertEqual(confirmed['passed'], ['0x1010'])
        current = ap.read_json(path)
        self.assertNotEqual(current['source']['digest'], previous['source']['digest'])
        self.assertEqual(current['submitter'], 'earlier-contributor')
        self.assertEqual(current['matchers'], previous['matchers'])
        self.assertNotEqual(current['source'], previous['source'])

    def test_cached_confirmation_restores_credit_without_recomparison(self):
        info = pr(author='Outside-Contributor', head=self.head, paths=(self.fixture.CPP,))
        result = ap.process(self.runtime, self.state, info, dry_run=True)
        tree = Path(result['completed']['fetch']['tree'])
        path = tree / self.fixture.RECORD
        record = ap.read_json(path)
        record.pop('submitter')
        ap.save_json(path, record)
        result['done'] = False
        self.state.save()
        comparisons = [c for c in self.commands if len(c) > 1 and c[1] == 'tools/verifier/confirm']
        models = list(self.models)
        ap.process(self.runtime, self.state, info, dry_run=True)
        self.assertEqual(ap.read_json(path)['submitter'], 'outside-contributor')
        self.assertEqual([c for c in self.commands if len(c) > 1 and c[1] == 'tools/verifier/confirm'], comparisons)
        self.assertEqual(self.models, models)

    def test_intake_acceptance_credits_pr_author_on_leaderboard(self):
        import flow
        import lane_accept
        import build_leaderboard as board
        result = ap.process(self.runtime, self.state,
                            pr(author='Outside-Contributor', head=self.head, paths=(self.fixture.CPP,)), dry_run=True)
        fetched = result['completed']['fetch']
        tree = Path(fetched['tree'])
        groups = result['completed']['reviews']['groups']
        requests = []
        for name in groups:
            group = flow.load_group(tree / '.local/flow', name)
            requests.append(dict(kind='review', review=str(flow.review_path(tree, group)),
                                 functions=group['functions'], profile='claude-low'))
        accepted = lane_accept.accept(tree, requests)
        self.assertFalse(accepted['dropped'])
        self.assertTrue(accepted['accepted'])
        record = ap.read_json(tree / self.fixture.RECORD)
        self.assertEqual(record['submitter'], 'outside-contributor')
        data = ap.read_json(tree / 'data/progress.json')
        rows = board.write(tree, data)
        self.assertEqual(rows[0]['contributor'], '@outside-contributor')
        self.assertEqual(rows[0]['functions'], 1)
        self.assertIn('@outside-contributor', (tree / 'LEADERBOARD.md').read_text())
        self.assertEqual(ap.read_json(tree / 'data/contributors.json')['contributors']['outside-contributor']['verified_matches'], 1)

    def test_dry_run_completes_with_pc_unavailable_and_wine_ci_profile(self):
        result = ap.process(self.runtime, self.state,
                            pr(head=self.head, paths=(self.fixture.CPP,)), dry_run=True)
        self.assertTrue(result['done'])
        published = result['completed']['publication']
        self.assertEqual(published['accepted'], 1)
        self.assertEqual(published['dropped'], 0)
        self.assertEqual(self.models, ['gpt-6.1-sol', 'gpt-6.1-terra', 'gpt-6.1-sol'])
        self.assertEqual(self.state.data['days'][self.state.today], dict(compiles=10, reviews=3))
        self.assertEqual(self.git('rev-parse', 'origin/main'), self.base)
        self.assertFalse((self.root / '.local/flow/lane/queue').exists())
        self.assertFalse((self.root / '.local/flow/groups').exists())
        for argv in self.commands:
            if argv[0] == 'gh':
                if argv[1] == 'api':
                    self.assertTrue(argv[-1].endswith('/check-runs') or '/actions/runs?' in argv[-1])
                else:
                    self.assertEqual(argv[1:3], ['pr', 'view'])
            if argv[0] == 'git':
                self.assertNotIn(argv[1], ('merge', 'commit-tree', 'push', 'commit'))
                if argv[1] == 'checkout':
                    self.assertEqual(argv[-1], self.base)
        tree = Path(result['completed']['fetch']['tree'])
        self.assertEqual(ap.read_json(tree / 'data/progress.json')['functions'][0]['status'], 'mapped')
        self.assertFalse((tree / self.fixture.REVIEW).exists())
        # Checkpointed dry run resumes without a second model call or compiler invocation.
        ap.process(self.runtime, ap.State(self.private, ap.DEFAULTS), pr(head=self.head, paths=(self.fixture.CPP,)), True)
        self.assertEqual(len(self.models), 3)

    def test_ci_determinism_compile_budget_is_reserved_before_sampling(self):
        self.state.config = dict(ap.DEFAULTS, daily_compiles=9)
        with self.assertRaises(ap.Limit):
            ap.process(self.runtime, self.state, pr(head=self.head, paths=(self.fixture.CPP,)), dry_run=True)
        self.assertEqual(self.state.data['days'][self.state.today]['compiles'], 6)
        self.assertEqual(sum(len(argv) > 1 and argv[1] in (
            'tools/verifier/attempt', 'tools/verifier/wine_confirm.py') for argv in self.commands), 2)

    def test_changed_accepted_unit_is_reconfirmed_reviewed_and_reaccepted(self):
        # Trusted main already accepted this member; the contributor edits its unit.
        # Its old approval must remain stale until new two-host records AND review bind it.
        import check
        self.kit.fn['status'] = 'matched'
        self.kit.save_review()
        self.kit.write('data/progress.json', json.dumps(self.kit.data))
        self.git('add', 'data/progress.json', self.fixture.REVIEW)
        self.git('commit', '--quiet', '-m', 'synthetic accepted baseline')
        self.git('push', '--quiet', 'origin', 'main')
        self.base = self.git('rev-parse', 'HEAD')
        result = ap.process(self.runtime, self.state,
                            pr(head=self.head, paths=(self.fixture.CPP,)), dry_run=True)
        self.assertEqual(result['completed']['companions'], {self.fixture.CPP: [0x1010]})
        self.assertEqual(result['completed']['confirmation']['passed'], ['0x1010'])
        self.assertEqual(result['completed']['reviews']['approved'], ['0x1010'])
        self.assertEqual(result['completed']['publication']['accepted'], 1)
        self.assertEqual(result['completed']['publication']['dropped'], 0)
        self.assertEqual(self.models, ['gpt-6.1-sol', 'gpt-6.1-terra', 'gpt-6.1-sol'])
        tree = Path(result['completed']['fetch']['tree'])
        fn = ap.read_json(tree / 'data/progress.json')['functions'][0]
        self.assertEqual(check.acceptance_staleness(fn, tree), check.STALE_REVIEW)

    def test_same_head_method_change_uses_new_tree_tasks_screens_and_groups(self):
        config = dict(ap.DEFAULTS, merge_method='merge')
        self.state.config = self.runtime.config = config
        row = pr(head=self.head, paths=(self.fixture.CPP,))
        legacy = ap.process(self.runtime, self.state, row, dry_run=True)
        config['merge_method'] = 'squash'
        squashed = ap.process(self.runtime, self.state, row, dry_run=True)
        self.assertNotEqual(legacy['completed']['fetch']['tree'], squashed['completed']['fetch']['tree'])
        self.assertNotEqual(legacy['completed']['export'], squashed['completed']['export'])
        self.assertNotEqual(legacy['completed']['groups'], squashed['completed']['groups'])
        self.assertEqual(squashed['completed']['fetch']['merge_method'], 'squash')
        self.assertEqual(squashed['completed']['publication']['accepted'], 1)
        self.assertEqual(squashed['completed']['publication']['dropped'], 0)
        self.assertEqual(len(self.models), 6)


class RecoveryRegression(unittest.TestCase):
    setUp = GitTransport.setUp
    git = GitTransport.git

    def test_reject_push_network_error_then_poll_uses_detail_not_stale_list(self):
        old = pr(72, 'outside', head='d' * 40)
        pushed = dict(pr(72, 'outside', head='e' * 40), state='OPEN')
        runtime = FakeRuntime()
        runtime.fetch = Mock(return_value=dict(problem='deterministic screen: include-outside-roots'))
        rejected = ap.process(runtime, self.state, old)
        self.assertTrue(rejected['done'])
        # Even after the push the REST discovery list keeps returning the rejected head.
        listing = [[dict(number=72, head=dict(sha=old['headRefOid']))]]
        self.runtime.command = Mock(return_value=subprocess.CompletedProcess([], 0, json.dumps(listing).encode(), b''))
        self.runtime.view_pr = Mock(side_effect=ap.Stop('error connecting to api.github.com'))
        with self.assertRaises(ap.Stop):
            self.runtime.list_prs()
        self.runtime.view_pr.side_effect = None
        self.runtime.view_pr.return_value = pushed
        observed = self.runtime.list_prs()
        self.assertEqual(observed, [pushed])
        saved = ap.State(self.private, ap.DEFAULTS).data['prs']['72']
        self.assertEqual(saved['head'], pushed['headRefOid'])
        self.assertFalse(saved.get('done'))
        self.assertEqual(saved['completed'], {})
        fresh = FakeRuntime()
        result = ap.process(fresh, self.state, observed[0])
        self.assertTrue(result['done'])
        self.assertEqual(fresh.calls, ['fetch', 'intake', 'functions', 'screen', 'export',
                                       'confirm', 'groups', 'reviews', 'publish', 'finish'])

    def test_new_revision_saved_before_another_detail_lookup_fails(self):
        self.state.revision(pr(72))['done'] = True
        self.state.save()
        listing = [[dict(number=72), dict(number=73)]]
        self.runtime.command = Mock(return_value=subprocess.CompletedProcess([], 0, json.dumps(listing).encode(), b''))
        self.runtime.view_pr = Mock(side_effect=[dict(pr(72, head='e' * 40), state='OPEN'), ap.Stop('network')])
        with self.assertRaises(ap.Stop):
            self.runtime.list_prs()
        saved = ap.State(self.private, ap.DEFAULTS).data['prs']['72']
        self.assertEqual(saved['head'], 'e' * 40)
        self.assertFalse(saved.get('done'))

    def test_stale_discovery_omission_revisits_saved_done_reopened_pr(self):
        self.state.revision(pr(72))['done'] = True
        self.state.save()
        self.runtime.command = Mock(return_value=subprocess.CompletedProcess([], 0, b'[[]]', b''))
        self.runtime.view_pr = Mock(return_value=dict(pr(72, head='e' * 40), state='OPEN'))
        self.assertEqual([p['number'] for p in self.runtime.list_prs()], [72])
        self.runtime.view_pr.return_value = dict(pr(72, head='e' * 40), state='CLOSED')
        self.assertEqual(self.runtime.list_prs(), [])

    def test_companion_confirmation_failure_holds_extension_before_review(self):
        runtime = FakeRuntime()
        runtime.accepted_companions = {'reconstruction/synth/Synth.cpp': [0x3000]}
        result = ap.process(runtime, self.state, pr(head=self.head))
        self.assertTrue(result['done'])
        self.assertNotIn('reviews', runtime.calls)
        self.assertNotIn('publish', runtime.calls)
        self.assertEqual(runtime.messages[-1][0], 'companion-confirmation')

    def test_companion_must_be_re_reviewed_before_extension_can_publish(self):
        for approved in ([], ['0x1000']):
            with self.subTest(approved=approved):
                runtime = FakeRuntime()
                runtime.accepted_companions = {'reconstruction/synth/Synth.cpp': [0x2000]}
                runtime.reviewed['approved'] = approved
                state = ap.State(self.private / str(len(approved)), ap.DEFAULTS)
                result = ap.process(runtime, state, pr(head=self.head))
                self.assertTrue(result['done'])
                self.assertNotIn('publish', runtime.calls)
                self.assertEqual(runtime.messages[-1][0], 'companion-review')
        runtime = FakeRuntime()
        runtime.accepted_companions = {'reconstruction/synth/Synth.cpp': [0x2000]}
        runtime.reviewed['approved'] = ['0x1000', '0x2000']
        state = ap.State(self.private / 'approved', ap.DEFAULTS)
        ap.process(runtime, state, pr(head=self.head))
        self.assertIn('publish', runtime.calls)

    def test_interrupted_initial_clone_is_retained_and_reinitialized(self):
        original = self.runtime.link_inputs
        with patch.object(self.runtime, 'link_inputs', side_effect=OSError('interrupted linking')):
            with self.assertRaises(OSError):
                self.runtime.fetch(pr(head=self.head))
        fetched = self.runtime.fetch(pr(head=self.head))
        tree = Path(fetched['tree'])
        self.assertTrue((tree / '.local/contrib-initialized.json').is_file())
        self.assertTrue(list(tree.parent.glob('tree-interrupted-*')))
        self.assertEqual(self.runtime.git(tree, 'rev-parse', 'HEAD'), self.base)

    def test_frozen_enqueued_revision_ignores_new_out_of_scope_metadata(self):
        runtime = FakeRuntime()
        runtime.crash = 'publish'
        with self.assertRaises(OSError):
            ap.process(runtime, self.state, pr(head=self.head))
        runtime.crash = None
        revised = pr(head='e' * 40, paths=('tools/attacker.py',))
        result = ap.process(runtime, self.state, revised)
        self.assertEqual(result['head'], self.head)
        self.assertIn('finish', runtime.calls)
        self.assertFalse(runtime.messages)

    def test_closed_unqueued_revision_is_abandoned_and_releases_contributor(self):
        runtime = FakeRuntime()
        result = ap.process(runtime, self.state, dict(pr(), state='CLOSED'))
        self.assertTrue(result['done'])
        self.assertTrue(result['abandoned'])
        self.assertFalse(runtime.calls)

    def test_scheduler_discovers_a_merged_pending_receipt(self):
        revision = self.state.revision(pr(head=self.head))
        revision['enqueued'] = True
        self.state.save()
        runtime = Mock()
        runtime.list_prs.return_value = []
        runtime.view_pr.return_value = dict(pr(head=self.head), state='MERGED')
        with patch.object(ap, 'Runtime', return_value=runtime), patch.object(ap, 'process', return_value={'done': True}) as process:
            self.assertEqual(ap.main(['--root', str(self.root), 'run-once']), 0)
        self.assertEqual(process.call_args.args[2]['state'], 'MERGED')
        runtime.require_account.assert_called_once()

    def test_transient_confirm_status_is_not_a_completed_negative(self):
        for code, output in [(2, b'configuration unavailable'), (1, b'  ERROR transport unavailable\n')]:
            with self.subTest(code=code), self.assertRaises(ap.Stop):
                ap.Runtime.require_comparison(subprocess.CompletedProcess([], code, output, b''))
        ap.Runtime.require_comparison(subprocess.CompletedProcess([], 1, b'NOT REPRODUCED host=fail\n', b''))

    def test_dry_reviews_do_not_enter_the_live_hold_store(self):
        self.runtime.dry_run = True
        fetched = self.runtime.fetch(pr(head=self.head))
        private_reviews = Path(fetched['tree']) / '.local/reviews'
        self.assertFalse(private_reviews.is_symlink())
        (private_reviews / 'dry-review.md').write_text('original synthetic rejection\n')
        self.assertFalse((self.root / '.local/reviews/dry-review.md').exists())


def _pid_running(pid):
    if sys.platform == 'win32':
        import csv
        result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                                capture_output=True, text=True, timeout=5)
        return any(len(row) > 1 and row[1] == str(pid) for row in csv.reader(result.stdout.splitlines()))
    result = subprocess.run(['ps', '-p', str(pid), '-o', 'stat='], capture_output=True, text=True, timeout=5)
    return result.returncode == 0 and not result.stdout.strip().startswith('Z')


class CompileSupervisorRegression(unittest.TestCase):
    def test_root_exit_still_terminates_descendant_holding_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            pidfile = Path(tmp) / 'child.pid'
            command = ('import subprocess,sys;from pathlib import Path;'
                       'p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(30)"]);'
                       f'Path({str(pidfile)!r}).write_text(str(p.pid))')
            started = time.monotonic()
            result = unit_build.compile_bounded([sys.executable, '-c', command], tmp, dict(os.environ), timeout=0.5)
            self.assertEqual(result.returncode, 0)
            self.assertLess(time.monotonic() - started, 4)
            self.assertFalse(_pid_running(int(pidfile.read_text())))

    def test_dead_outer_supervisor_does_not_cancel_the_child_deadline(self):
        with tempfile.TemporaryDirectory() as tmp:
            pidfile = Path(tmp) / 'child.pid'
            # Existence signals readiness to kill the outer supervisor. Publish the
            # complete PID atomically so the reader cannot observe an empty file.
            payload = ('import os,time;from pathlib import Path;'
                       f'p=Path({str(pidfile)!r});'
                       'p.with_suffix(".tmp").write_text(str(os.getpid()));'
                       'p.with_suffix(".tmp").replace(p);time.sleep(30)')
            runner = ('import os,sys;sys.path.insert(0,' + repr(str(ROOT / 'tools/verifier')) + ');'
                      'import unit_build;unit_build.compile_bounded('
                      + repr([sys.executable, '-c', payload]) + ',' + repr(tmp) + ',dict(os.environ),timeout=0.5)')
            proc = subprocess.Popen([sys.executable, '-c', runner], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                deadline = time.monotonic() + 3
                while not pidfile.exists() and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertTrue(pidfile.exists())
                pid = int(pidfile.read_text())
                proc.kill()
                proc.wait(timeout=2)
                deadline = time.monotonic() + 3
                while _pid_running(pid) and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertFalse(_pid_running(pid))
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=2)

    def test_failed_windows_job_setup_never_launches_a_compiler(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(unit_build.sys, 'platform', 'win32'), \
                patch.object(unit_build, 'windows_compile_job', side_effect=OSError('job refused')), \
                patch.object(unit_build.subprocess, 'run', side_effect=AssertionError('must not compile')):
            result = Path(tmp) / 'result.json'
            self.assertEqual(unit_build.compile_supervisor(['unused'], 0.1, result), 125)
            self.assertTrue(json.loads(result.read_text())['supervisor_error'])


# Exercise an actual transport refusal at both confirmation stages in the end-to-end fixture.
def _test_transient_confirm_resume(self):
    original = self.runtime.command
    count = 0
    def command(argv, **kwargs):
        nonlocal count
        if len(argv) > 1 and argv[1] == 'tools/verifier/confirm':
            count += 1
            if count == 1:
                return subprocess.CompletedProcess(argv, 2, b'transport unavailable', b'')
        return original(argv, **kwargs)
    self.runtime.command = command
    row = pr(head=self.head, paths=(self.fixture.CPP,))
    with self.assertRaises(ap.Stop):
        ap.process(self.runtime, self.state, row, True)
    self.assertNotIn('confirmation', self.state.revision(row, True)['completed'])
    result = ap.process(self.runtime, self.state, row, True)
    self.assertEqual(result['completed']['publication']['accepted'], 1)
    self.assertEqual(self.models, ['gpt-6.1-sol', 'gpt-6.1-terra', 'gpt-6.1-sol'])


SyntheticEndToEnd.test_transient_confirmation_resumes_same_head = _test_transient_confirm_resume


class EnqueueIntentRegression(unittest.TestCase):
    setUp = RuntimeEffects.setUp

    def crash_after_real_enqueue(self):
        import flow_lane
        fake = FakeRuntime()
        original_fetch = fake.fetch
        def fetch(row):
            result = original_fetch(row)
            result['tree'] = str(self.root / 'tree')
            return result
        fake.fetch = fetch
        fake.publish = self.runtime.publish
        self.runtime.current_head = lambda number: 'a' * 40
        def command(argv, **kwargs):
            self.assertEqual(argv[1:3], ['tools/flow.py', 'integrate'])
            flow_lane.enqueue(self.root / 'tree', self.runtime.fdir, 'review', ['g1'], approved_only=True)
            raise OSError('crash after real durable enqueue, before returning to autopilot')
        self.runtime.command = command
        with self.assertRaises(OSError):
            ap.process(fake, self.state, pr())
        self.state = ap.State(self.private, ap.DEFAULTS)
        revision = self.state.data['prs']['1']
        self.assertTrue(revision['enqueued'])
        self.assertTrue(list((self.runtime.fdir / 'lane/queue').glob('*.json')))
        self.assertNotIn('publication', revision['completed'])
        fake.publish = FakeRuntime.publish.__get__(fake, FakeRuntime)
        return fake

    def test_enqueue_crash_then_new_head_keeps_frozen_receipt(self):
        fake = self.crash_after_real_enqueue()
        result = ap.process(fake, self.state, pr(head='e' * 40, paths=('tools/attacker.py',)))
        self.assertEqual(result['head'], 'a' * 40)
        self.assertTrue(result['done'])
        self.assertIn('finish', fake.calls)
        self.assertFalse(fake.messages)

    def test_enqueue_crash_then_merged_pr_still_finishes_receipt(self):
        fake = self.crash_after_real_enqueue()
        result = ap.process(fake, self.state, dict(pr(), state='MERGED'))
        self.assertTrue(result['done'])
        self.assertNotIn('abandoned', result)
        self.assertIn('finish', fake.calls)


if __name__ == '__main__':
    unittest.main()


class WaitingFeedbackTests(unittest.TestCase):
    def test_waiting_feedback_is_fixed_sanitized_and_uses_existing_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = ap.State(root, ap.DEFAULTS)
            with patch.object(ap, 'shared_root', return_value=root):
                runtime = ap.Runtime(root, root, ap.DEFAULTS, state, dry_run=True)
            revision = state.revision(pr(), True)
            runtime.waiting(revision, 'timeout')
            body = revision['would_post']['waiting-timeout']['body']
            self.assertIn('timed out', body)
            self.assertIn('<!-- contrib-autopilot:', body)
            self.assertIsNone(revision['would_post']['waiting-timeout']['label'])
            self.assertNotIn(str(root), body)
            runtime.waiting(revision, 'daily-budget')
            self.assertIn('next UTC day', revision['would_post']['waiting-daily-budget']['body'])

    def test_failed_feedback_preserves_retry_state_without_losing_the_pr(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = ap.State(root, ap.DEFAULTS)
            with patch.object(ap, 'shared_root', return_value=root):
                runtime = ap.Runtime(root, root, ap.DEFAULTS, state)
            revision = state.revision(pr())
            with patch.object(runtime, 'feedback', side_effect=ap.Stop('private transport detail')):
                runtime.waiting(revision, 'service-retry')
            saved = ap.State(root, ap.DEFAULTS).data['prs']['1']
            self.assertTrue(saved['waiting_feedback_pending'])
            self.assertEqual(saved['waiting_reason'], 'service-retry')
            self.assertFalse(saved.get('done'))

class StructuredFeedbackTests(unittest.TestCase):
    def test_lessons_are_documented_and_safe(self):
        doc = (ROOT / 'docs/contributor-lessons.md').read_text()
        for lesson, reference in ap.LESSONS.values():
            self.assertIn(f'{lesson} ({reference})', doc)
            self.assertEqual(ap.safe_reason(f'{lesson} ({reference})'), f'{lesson} ({reference})')

    def test_accepted_and_rejected_render_and_filter(self):
        rev = {'feedback_public_rvas': ['0x1000'], 'feedback_names': {'0x1000': 'Synthetic'},
               'completed': {'functions': {'unit.cpp': [4096]},
                             'confirmation': {'passed': ['0x1000']}, 'reviews': {'approved': ['0x1000']}}}
        rev['feedback_results'] = {'0x1000': 'matched, confirmed on 2 hosts, reviewed, merged'}
        accepted = ap.render_outcome(rev, '')
        self.assertIn('matched, confirmed on 2 hosts', accepted)
        self.assertIn('<!-- agent-lessons:start -->', accepted)
        rejected = ap.render_outcome(rev, 'opaque storage\n/Users/private/secret\n0x12345678')
        self.assertIn('Never pad a base class', rejected)
        self.assertIn('Details withheld by the publication filter', rejected)
        self.assertNotIn('/Users/private', rejected)
        self.assertNotIn('0x12345678', rejected)
        for line in rejected.splitlines():
            if line.strip():
                self.assertEqual(ap.safe_reason(line), line)
