"""Deterministic meta-tool acceptance tests. No target server, host or portal is contacted."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/prepare-plugin-submission/scripts'
FX = ROOT / 'tests/fixtures'
sys.path.insert(0, str(SCRIPTS))
import check_package
import workflow_core as core
import host_reports
import audit_target


class Preflight(unittest.TestCase):
    def checker(self, target, **kwargs):
        return check_package.Checker(check_package.load_files(target), 'openai', 'submission', **kwargs).run()

    def cli(self, *args, expected=0):
        p = subprocess.run([sys.executable,str(SCRIPTS/'prepare_workflow.py'),*map(str,args)],capture_output=True,text=True)
        self.assertEqual(p.returncode,expected,p.stdout+p.stderr)
        return json.loads(p.stdout or p.stderr)

    def test_broken_zip_finds_actual_errors(self):
        result = self.checker(FX/'broken-plugin.zip',synthetic=True)
        self.assertEqual(result['status'],'local_checks_failed')
        self.assertTrue(any('version' in i['code'] for i in result['issues']))
        self.assertTrue(any('skill' in i['code'] for i in result['issues']))
        self.assertFalse(result['ready_to_submit'])

    def test_local_default_and_missing_confirmation_fail(self):
        self.assertTrue(any(i['code']=='remote_required' for i in self.checker(FX/'desktop-stdio')['issues']))
        result=self.checker(FX/'desktop-stdio',submission_route='desktop-only')
        self.assertTrue(any(i['code']=='desktop_allowlist_required' for i in result['issues']))

    def test_desktop_fixture_is_permitted_without_remote_review(self):
        record=json.loads((FX/'desktop-allowlist.json').read_text())
        result=self.checker(FX/'desktop-stdio',submission_route='desktop-only',desktop_allowlist=record,synthetic=True)
        self.assertEqual(result['status'],'local_checks_passed',result['issues'])
        self.assertTrue(result['desktop_allowlist']['record_accepted'])
        self.assertFalse(result['ready_to_submit'])
        self.assertFalse(any(i['code'] in ('review_case_count','remote_required') for i in result['issues']))
        self.assertIn('Publication',result['human_handoffs'])

    def test_synthetic_confirmation_is_rejected_in_normal_runs(self):
        result=self.checker(FX/'desktop-stdio',submission_route='desktop-only',desktop_allowlist=json.loads((FX/'desktop-allowlist.json').read_text()))
        self.assertTrue(any(i['code']=='synthetic_allowlist_rejected' for i in result['issues']))

    def test_incomplete_allowlist_record_is_rejected(self):
        record=json.loads((FX/'desktop-allowlist.json').read_text());record.pop('organization_id')
        result=self.checker(FX/'desktop-stdio',submission_route='desktop-only',desktop_allowlist=record,synthetic=True)
        self.assertTrue(any(i['code']=='desktop_allowlist_required' for i in result['issues']))

    def test_review_prep_is_static_and_conditional(self):
        good=self.checker(FX/'review-prep.zip',synthetic=True)
        self.assertEqual(good['status'],'local_checks_passed',good['issues'])
        self.assertFalse(good['ready_to_submit'])
        self.assertTrue(good['synthetic'])
        normal=self.checker(FX/'review-prep.zip')
        self.assertTrue(any(i['code']=='public_https_required' for i in normal['issues']))
        files=check_package.load_files(FX/'review-prep.zip');manifest=json.loads(files['plugin.json'])
        manifest['extensions']['com.openai']['review']['test_cases']['positive'].pop()
        files['plugin.json']=json.dumps(manifest).encode()
        bad=check_package.Checker(files,'openai','submission',synthetic=True).run()
        self.assertTrue(any(i['code']=='review_case_count' for i in bad['issues']))

    def test_loaded_audit_populates_documents_but_not_host_claims(self):
        with tempfile.TemporaryDirectory(dir=ROOT.parent) as d:
            out=Path(d)/'audit';self.cli('audit','--source',ROOT,'--output',out)
            self.cli('check',out)
            rows=json.loads((out/'readiness/requirements.json').read_text())['requirements']
            self.assertEqual(len(rows),49)
            self.assertTrue(all(r['source_checked_at'] and r['observed_result'] and r['evidence'] for r in rows))
            for row in rows:
                self.assertTrue((out/row['evidence'][0]).is_file())
            docs=[p for p in out.rglob('*.md') if p.name not in ('review.md',)]
            self.assertEqual(len(docs),13)
            self.assertTrue(all('Complete from inspected source' not in p.read_text() for p in docs))
            observed=json.loads((out/'evidence/source-inspection.json').read_text())['observed']
            self.assertFalse(observed['portal_actions_performed'])
            self.assertFalse(observed['source_executed'])
            self.assertEqual(json.loads((out/'submission/publication-state.json').read_text())['published'],False)
            self.assertTrue(any(r['status']=='Not applicable' for r in rows))
            self.assertTrue(any(r['status']=='Not run' for r in rows))

    def test_loaded_desktop_and_review_records_keep_target_facts(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            desktop=d/'desktop';self.cli('audit','--source',FX/'desktop-stdio','--output',desktop,'--synthetic',
                                       '--profile','submission','--submission-route','desktop-only',
                                       '--desktop-allowlist',FX/'desktop-allowlist.json')
            rows={r['requirement_id']:r for r in json.loads((desktop/'readiness/requirements.json').read_text())['requirements']}
            self.assertEqual(rows['SS-ARCH-03']['status'],'Not applicable')
            self.assertEqual(rows['SS-SKILL-01']['status'],'Not applicable')
            facts=json.loads((desktop/'integration.json').read_text())
            self.assertEqual(facts['server']['connection']['transport'],'stdio')
            report=json.loads((desktop/'evidence/package-check.json').read_text())
            self.assertTrue(report['desktop_allowlist']['record_accepted'])
            self.assertEqual(report['status'],'local_checks_passed')
            self.assertEqual(rows['SS-ARCH-02']['status'],'Not run')
            self.assertEqual(json.loads((desktop/'submission/review-cases.json').read_text())['status'],'Not applicable')
            readiness=json.loads((desktop/'readiness/record.json').read_text())
            self.assertFalse(any(f['code']=='connection_unknown' for f in readiness['findings']))
            self.assertNotIn('The target is assessed as a preflight auditing meta-tool',(desktop/'architecture/assessment.md').read_text())
            self.assertIn('do not apply to this local-only desktop package',(desktop/'submission/demo-plan.md').read_text())
            self.assertNotIn('Recording and secure reviewer access remain human handoffs',(desktop/'submission/demo-plan.md').read_text())
            review=d/'review';self.cli('audit','--source',FX/'review-prep.zip','--output',review,'--synthetic')
            cases=json.loads((review/'submission/review-cases.json').read_text())['cases']
            self.assertEqual(sum(c['kind']=='positive' for c in cases),5)
            self.assertEqual(sum(c['kind']=='negative' for c in cases),3)
            self.assertEqual(json.loads((review/'integration.json').read_text())['server']['connection']['url'],'https://fixture.invalid/mcp')
            demo=(review/'submission/demo-plan.md').read_text()
            self.assertIn('https://fixture.invalid/demo',demo)
            self.assertIn('Playback and access were not checked',demo)
            self.assertIn('synthetic fixture metadata',demo)
            self.assertNotIn('audit the broken ZIP',demo)

    def test_audit_submission_route_does_not_bypass_confirmation(self):
        with tempfile.TemporaryDirectory() as d:
            result=self.cli('audit','--source',FX/'desktop-stdio','--output',Path(d)/'desktop',
                            '--profile','submission','--submission-route','desktop-only','--synthetic',expected=1)
            self.assertTrue(any(i['code']=='desktop_allowlist_required' for i in result['findings']))

    def test_loaded_broken_zip_retains_findings_and_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/'broken'
            result=self.cli('audit','--source',FX/'broken-plugin.zip','--output',output,expected=1)
            self.assertEqual(result['target_preflight_status'],'local_checks_failed')
            self.assertTrue(result['findings'])
            self.assertIn('unresolved package errors',(output/'operations/deployment.md').read_text())

    def test_catalog_covers_every_inventory_topic_and_native_cases_match(self):
        import re
        lifecycle=(ROOT/'skills/prepare-plugin-submission/references/openai-lifecycle.md').read_text()
        section=lifecycle[lifecycle.index('## 2. Official'):lifecycle.index('## 3. Requirement')]
        topics={u for u in re.findall(r'https://[^)\s]+',section) if not u.endswith(('llms.txt','llms-full.txt')) and u!='https://developers.openai.com/plugins'}
        catalog=json.loads((ROOT/'skills/prepare-plugin-submission/references/requirements.json').read_text())['requirements']
        self.assertTrue(topics <= {r['source_url'] for r in catalog})
        cases=json.loads((ROOT/'evals/cases.json').read_text())
        self.assertEqual({c['id'] for c in cases},{p.parent.name for p in (ROOT/'evals').glob('*/prompt.md')})

    def report_fixture(self,directory,origin='synthetic'):
        facts=dict(schema_version=1,id='host-fixture',name='Host fixture',source_revision='fixture-v1',platform='openai',hosts=['chatgpt','codex'],
                   components={'mcp':False,'skills':True},server={},tools=[],cases=[],package_sha256='a'*64,
                   host_cases=[{'id':'skill-case','prompt':'Audit the supplied sample','expected':'Identify the fixture defect'}])
        plan=core.test_plan(facts)
        report=dict(schema_version=1,report_kind='product-host',host='chatgpt',origin=origin,binding=plan['binding'],package_sha256='a'*64,
                    observer='Synthetic test author',observed_at='2026-10-16T11:00:00Z',environment={'host_version':'fixture','runner_version':'unit-test'},cases=[])
        capture=dict(binding=plan['binding'],package_sha256='a'*64,host='chatgpt',origin=origin,case_id='skill-case',status='Passed',
                     expected='Identify the fixture defect',observed='Fixture defect identified',assessment_rationale='Controlled parser fixture, not a real host run',tool_calls=[],side_effects={'expected':'none','observed':'none'})
        file=Path(directory)/'capture.json';file.write_text(json.dumps(capture))
        report['cases']=[dict(id='skill-case',status='Passed',expected=capture['expected'],evidence={'file':'capture.json','sha256':hashlib.sha256(file.read_bytes()).hexdigest()})]
        return facts,plan,report,Path(directory)/'report.json'

    def test_product_host_contract_accepts_both_surfaces(self):
        with tempfile.TemporaryDirectory() as d:
            _,plan,report,path=self.report_fixture(d)
            for host in ('chatgpt','codex'):
                report['host']=host;p=Path(d)/'capture.json';capture=json.loads(p.read_text());capture['host']=host;p.write_text(json.dumps(capture))
                report['cases'][0]['evidence']['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
                rows=host_reports.validate_report(report,path,plan)
                self.assertEqual(rows[0]['surface'],host)
                self.assertEqual(rows[0]['origin'],'synthetic')

    def test_host_contract_rejects_stale_unknown_and_tampered_data(self):
        with tempfile.TemporaryDirectory() as d:
            _,plan,report,path=self.report_fixture(d)
            for mutation in ('binding','digest','host','case','escape','expected'):
                value=copy.deepcopy(report)
                if mutation=='binding':value['binding']['source_revision']='stale'
                elif mutation=='digest':value['cases'][0]['evidence']['sha256']='b'*64
                elif mutation=='host':value['host']='unknown-host'
                elif mutation=='case':value['cases'][0]['id']='unknown-case'
                elif mutation=='escape':value['cases'][0]['evidence']['file']='../capture.json'
                else:value['cases'][0]['expected']='Invented expectation'
                with self.subTest(mutation=mutation),self.assertRaises(ValueError):host_reports.validate_report(value,path,plan)

    def test_synthetic_ingestion_cannot_verify_a_host(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);facts,_,_,_=self.report_fixture(d)
            inp=d/'facts.json';inp.write_text(json.dumps(facts));out=d/'pack';self.cli('prepare','--input',inp,'--output',out)
            plan=json.loads((out/'plan.json').read_text())
            _,_,report,path=self.report_fixture(d);report['binding']=plan['binding']
            capture_path=d/'capture.json';capture=json.loads(capture_path.read_text());capture['binding']=plan['binding'];capture_path.write_text(json.dumps(capture))
            report['cases'][0]['evidence']['sha256']=hashlib.sha256(capture_path.read_bytes()).hexdigest();path.write_text(json.dumps(report))
            result=self.cli('assess',out,'--report',path,expected=2)
            self.assertEqual(result['synthetic_cases_validated'],1)
            self.assertFalse(result['synthetic_is_host_verification'])
            self.assertTrue(all(r['status']=='Not run' for r in result['coverage']))

    def test_capture_requires_explicit_calls_effects_and_unique_fields(self):
        with tempfile.TemporaryDirectory() as d:
            _,plan,report,path=self.report_fixture(d)
            capture_path=Path(d)/'capture.json';original=json.loads(capture_path.read_text())
            for mutation in ('calls','effects','duplicate','nonobject'):
                value=copy.deepcopy(original)
                if mutation=='calls':value.pop('tool_calls')
                elif mutation=='effects':value['side_effects'].pop('observed')
                data=(json.dumps(value)[:-1]+',"status":"Passed"}' if mutation=='duplicate' else
                      '[]' if mutation=='nonobject' else json.dumps(value))
                capture_path.write_text(data)
                report['cases'][0]['evidence']['sha256']=hashlib.sha256(capture_path.read_bytes()).hexdigest()
                with self.subTest(mutation=mutation),self.assertRaises(ValueError):host_reports.validate_report(report,path,plan)


if __name__=='__main__':unittest.main()
