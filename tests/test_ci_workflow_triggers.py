import unittest
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parents[1] / '.github/workflows'


class CheckWorkflowTriggers(unittest.TestCase):
    def test_candidate_branches_do_not_run_the_full_suite(self):
        text = (WORKFLOWS / 'check.yml').read_text()
        head = text.split('permissions:')[0]
        self.assertIn("branches-ignore: ['ci-confirm/**']", head)
        self.assertNotIn('\n    branches:', head)

    def test_main_pushes_still_trigger_the_checks_that_gates_read(self):
        head = (WORKFLOWS / 'check.yml').read_text().split('permissions:')[0]
        self.assertIn('\n  push:', head)
        self.assertIn('\n  pull_request:', head)

    def test_no_tool_waits_for_checks_on_a_confirm_branch(self):
        tools = Path(__file__).resolve().parents[1] / 'tools'
        pusher = (tools / 'verifier/ci_confirm.py').read_text()
        self.assertIn("refs/heads/ci-confirm/", pusher)
        self.assertNotIn('Infrastructure', pusher)
        self.assertNotIn('ci_status', pusher)


class PrCheckWorkflow(unittest.TestCase):
    text = (WORKFLOWS / 'pr-check.yml').read_text()

    def test_untrusted_compile_runs_under_pull_request_with_a_read_only_token(self):
        self.assertIn('\n  pull_request:', self.text)
        self.assertNotIn('pull_request_target', self.text)
        self.assertIn('permissions:\n  contents: read', self.text)
        self.assertNotIn('secrets.', self.text)

    def test_trusted_tools_come_from_the_base_revision(self):
        self.assertEqual(self.text.count('ref: ${{ github.event.pull_request.base.sha }}'), 2)

    def test_both_jobs_exist_and_hash_blocks_only_through_regress(self):
        self.assertIn('\n  scope:', self.text)
        self.assertIn('\n  hash:', self.text)
        self.assertIn('ci_target_hash_check.py regress', self.text)
        self.assertIn('tools/leakgrep.py', self.text)


if __name__ == '__main__':
    unittest.main()
