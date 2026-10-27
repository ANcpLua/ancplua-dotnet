"""Run with python3 -m unittest discover -s evals/runtime -v from plugin root."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'skills/prepare-plugin-submission/scripts'
sys.path.insert(0, str(SCRIPTS))
import workflow_core as core
import openai_core


class Workflows(unittest.TestCase):
    def facts(self):
        return dict(schema_version=1, id='sample', name='Sample', source_revision='fixture-v1',
                    platform='openai', hosts=['chatgpt', 'codex'], server={}, tools=[], cases=[],
                    components=dict(mcp=False, skills=True, ui=False))

    def run_cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, str(SCRIPTS / 'prepare_workflow.py'), *map(str, args)], capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stderr + result.stdout)
        return json.loads(result.stdout or result.stderr)

    def test_openai_skills_only_is_not_remote_server(self):
        facts = core.validate_input(self.facts())
        r = core.readiness(facts, core.test_plan(facts))
        self.assertEqual(r['platform'], 'openai')
        self.assertFalse(r['live_verification_performed'])
        self.assertFalse(any(f['code'] == 'connection_unknown' for f in r['findings']))
        self.assertTrue(all(c['status'] == 'Not applicable' for c in r['auth_checks']))
        self.assertFalse(core.policy_matrix(facts)['legal_compliance_certified'])
        self.assertNotIn('claude.com', json.dumps(core.policy_matrix(facts)))

    def test_cross_platform_must_be_selected(self):
        facts = self.facts(); facts['hosts'] = ['claude-code']
        with self.assertRaises(ValueError): core.validate_input(facts)
        facts['platform'] = 'claude'
        self.assertEqual(core.validate_input(facts)['platform'], 'claude')
        self.assertIn('claude.com', core.SOURCES['server'])

    def test_missing_fixtures_block_execution(self):
        facts = self.facts(); facts['tools'] = [dict(name='real_tool')]
        plan = core.test_plan(facts)
        self.assertEqual({c['kind'] for c in plan['cases']}, {'valid', 'invalid'})
        self.assertTrue(all(c['arguments'] is None and c['expected'] is None for c in plan['cases']))
        records = openai_core.handoff_records(facts, plan)
        self.assertEqual(records['protocol/negotiation-results.json']['observed_era'], None)
        self.assertEqual(records['protocol/supported-versions.json']['claimed_versions'], [])

    def test_pack_integrity_and_unknown_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory); inp = d/'input.json'; inp.write_text(json.dumps(self.facts()))
            out = d/'pack'; self.run_cli('prepare', '--input', inp, '--output', out)
            self.run_cli('check', out)
            requirements = json.loads((out/'readiness/requirements.json').read_text())['requirements']
            self.assertTrue(requirements)
            self.assertTrue(all(r['source_checked_at'] and r['status'] == 'Not run' for r in requirements))
            self.assertFalse((out/'postlaunch/check_health.py').exists())
            self.assertEqual(json.loads((out/'protocol/negotiation-results.json').read_text())['status'], 'Not applicable')
            self.run_cli('assess', out, expected=2)
            (out/'submission/listing.md').write_text('Changed after hashing')
            self.assertEqual(self.run_cli('check', out, expected=1)['status'], 'Failed')

    def test_defaults_starter_and_explicit_claude(self):
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory); inp = d/'input.json'
            self.run_cli('init', '--id', 'sample', '--output', inp)
            self.assertEqual(json.loads(inp.read_text())['platform'], 'openai')
            self.run_cli('init', '--id', 'sample', '--output', inp, expected=2)
            out = d/'starter'; self.run_cli('starter', '--output', out)
            facts = json.loads((out/'integration.json').read_text())
            self.assertEqual(facts['hosts'], ['chatgpt','codex'])
            self.assertFalse(json.loads((out/'production-gaps.json').read_text())['runtime_verified'])
            self.assertNotIn('@modelcontextprotocol/sdk', (out/'package.json').read_text())
            ci = d/'claude.json'; self.run_cli('init','--id','sample','--platform','claude','--output',ci)
            co = d/'claude'; self.run_cli('prepare','--input',ci,'--output',co)
            self.assertIn('claude.com', json.dumps(json.loads((co/'readiness/record.json').read_text())['sources']))
            self.assertTrue((co/'postlaunch/check_health.py').is_file())
            result = subprocess.run([sys.executable,str(co/'postlaunch/check_health.py'),str(co/'postlaunch/health-input.json')],capture_output=True,text=True)
            self.assertIn('Unknown',result.stdout)


if __name__ == '__main__': unittest.main()
