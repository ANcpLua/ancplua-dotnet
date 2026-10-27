"""Guided journeys use synthetic inputs. No host, endpoint or portal is operated."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/prepare-plugin-submission/scripts'
FX = ROOT / 'tests/fixtures'
sys.path.insert(0, str(SCRIPTS))
import wizard_core as core
import wizard
import check_package


class Wizard(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT.parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.session = self.root / 'session.json'
        self.response = self.root / 'response.json'
        self.docs=self.root/'docs.json'
        self.docs.write_text(json.dumps({'origin':'observed','documents':[dict(url='https://developers.openai.com/plugins/deploy/desktop-only',
            text='# Synthetic desktop policy fixture\nLocal MCP organizations must be allowlisted.',
            provider='deterministic test fixture',observed_at='2026-10-16T12:00:00Z')]}))

    def run_cli(self, *args, expected=0):
        p = subprocess.run([sys.executable, str(SCRIPTS/'wizard.py'), *map(str, args)],
            capture_output=True, text=True, env={**os.environ, 'TMPDIR': str(self.root), 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertEqual(p.returncode, expected, p.stdout+p.stderr)
        return json.loads(p.stdout or p.stderr)

    def start(self, source=None, synthetic=True, hosts=('chatgpt',), goal='public-submission', *extra):
        args = ['start', '--session', self.session,'--docs-mode','offline','--docs-input',self.docs]
        if source: args += ['--source', source]
        if synthetic: args += ['--synthetic']
        if goal: args += ['--goal', goal]
        for host in hosts: args += ['--host', host]
        return self.run_cli(*args, *extra)

    def answer(self, step, value, expected=0):
        if step=='test-plan':
            current=self.run_cli('next','--session',self.session)
            if current['next']['id']=='understanding':self.accept_setup()
            current=self.run_cli('next','--session',self.session)
            if current['next']['id']=='independent-review':self.unavailable_review()
            if self.run_cli('next','--session',self.session)['next']['id']!='test-plan':
                self.run_cli('revisit','--session',self.session,'--step','test-plan')
        self.response.write_text(json.dumps(value))
        result=self.run_cli('answer', '--session', self.session, '--step', step, '--input', self.response, expected=expected)
        if step=='test-plan' and expected==0 and result['next']['id']=='independent-review':
            result=self.unavailable_review()  # A changed plan creates a new bound review request.
        return result

    def state(self):
        return json.loads(self.session.read_text())

    def accept_setup(self):
        q=self.state()['question_plan']
        self.response.write_text(json.dumps(dict(question_id=q['id'],revision=q['revision'],selected=['accept'])))
        return self.run_cli('choose','--session',self.session,'--input',self.response)

    def unavailable_review(self):
        s=self.state();job=s['jobs']['independent-review']
        self.response.write_text(json.dumps(dict(status='Unavailable',reason='Controlled regression has no independent host provider',
            binding=core.binding(s),docs_sha256=s['docs']['content_sha256'],request_sha256=job['request_sha256'])))
        return self.run_cli('review','--session',self.session,'--input',self.response)

    def seed_finding(self, classification='official_requirement'):
        s=self.state();s['findings']=[dict(id='controlled-finding',classification=classification,severity='error',status='Failed',
            source_path='plugin.json',message='Controlled unresolved observation',fix='Resolve the controlled observation',
            summary='Controlled fixture',scope='any',source_url='https://developers.openai.com/plugins/deploy/submission')]
        self.session.write_text(json.dumps(s))

    def plan_cases(self):
        cases = self.state()['snapshot']['review_cases']
        return [{'id': 'case-'+str(n), 'prompt': c['prompt'],
                 'expected': c.get('expected_behavior', 'Refuse the unsupported action without side effects.')}
                for n, c in enumerate(cases)] or [{'id':'main-workflow','prompt':'Run the declared fixture workflow',
                                                  'expected':'Return the controlled fixture result.'}]

    def import_capture(self, host='chatgpt', origin='synthetic', status='Passed', tamper=False):
        state = self.state(); plan = json.loads(Path(state['artifacts']['plan']).read_text())
        folder = self.root / ('report-'+host+'-'+str(len(list(self.root.glob('report-*')))))
        folder.mkdir()
        report = dict(schema_version=1, report_kind='product-host', host=host, origin=origin,
            binding=plan['binding'], package_sha256=plan['package_sha256'], observer='Synthetic fixture author',
            observed_at='2026-10-16T12:00:00Z', environment={'host_version':'synthetic','runner_version':'unit-test'}, cases=[])
        for case in plan['host_cases']:
            capture = dict(binding=plan['binding'], package_sha256=plan['package_sha256'], host=host,
                origin=origin, case_id=case['id'], status=status, expected=case['expected'],
                observed='Controlled synthetic capture', assessment_rationale='Parser/state-machine fixture; no host execution',
                tool_calls=[], side_effects={'expected':'none','observed':'none'})
            path = folder / (case['id']+'.json'); path.write_text(json.dumps(capture))
            report['cases'].append(dict(id=case['id'],status=status,expected=case['expected'],
                evidence={'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}))
        if tamper: report['binding']['source_revision']='different-target'
        path = folder/'report.json'; path.write_text(json.dumps(report))
        return self.run_cli('ingest','--session',self.session,'--report',path,expected=2 if tamper else 0)

    def finish_preparation(self):
        result = self.run_cli('next','--session',self.session)
        while result['next']['id'] not in ('upload','done'):
            step = result['next']['id']
            if step=='test-plan': result=self.answer(step,{'cases':self.plan_cases()})
            elif step=='understanding':result=self.accept_setup()
            elif step=='independent-review':result=self.unavailable_review()
            elif step=='host-tests':
                result=self.import_capture()
                if 'codex' in self.state()['answers']['hosts']['hosts']:result=self.import_capture('codex')
            elif step=='review-materials': result=self.answer(step,{'recording_accessible':True,'reviewer_access_ready':True,'confirmed_by':'Fixture','reference':'synthetic:demo-access'})
            elif step=='desktop-install': result=self.answer(step,{'confirmed':True,'confirmed_by':'Fixture','reference':'synthetic:desktop-install'})
            elif step=='requirement-review':
                state=self.state();source=next(r for r in state['snapshot']['facts']['audit_inventory'] if r['path']=='plugin.json')
                rows=[dict(id=r['id'],status='Passed',observed_result='Synthetic gate exercise; not an integration verification',evidence_reference='synthetic:requirement-fixture',evidence={'source_path':'plugin.json','sha256':source['sha256']}) for r in result['next']['requirements']]
                result=self.answer(step,{'decisions':rows})
            elif step=='creator-facts': result=self.answer(step,dict(publisher=True,rights=True,data_practices=True,support=True,confirmed_by='Fixture',reference='synthetic:creator-confirmation'))
            else:self.fail('Unexpected preparation step '+step)
        return result

    def portal_response(self, step, **extra):
        return dict(confirmed=True, confirmed_by='Fixture', reference='synthetic:'+step,
            plugin_reference='synthetic-plugin', release_reference='synthetic-release', **extra)

    def test_unloaded_session_is_an_interactive_source_question(self):
        result=self.start(goal=None,hosts=())
        self.assertEqual(result['next']['id'],'source')
        self.assertFalse(result['ready_for_human_portal'])
        self.assertFalse(result['published'])

    def test_broken_target_drives_a_concrete_repair(self):
        result=self.start(FX/'broken-plugin.zip')
        self.assertEqual(result['next']['id'],'package')
        self.assertTrue(result['next']['findings'])
        self.assertFalse(result['ready_for_human_portal'])
        self.answer('upload',self.portal_response('upload'),expected=2)

    def test_audit_goal_finishes_with_findings_without_portal_gates(self):
        result=self.start(FX/'broken-plugin.zip',goal='audit',hosts=())
        self.assertEqual(result['next']['id'],'done')
        self.assertTrue(result['next']['findings'])
        self.assertFalse(result['ready_for_human_portal'])

    def test_complete_synthetic_remote_journey_never_claims_real_publication(self):
        self.start(FX/'review-prep.zip',hosts=('chatgpt','codex'))
        result=self.finish_preparation()
        self.assertEqual(result['next']['id'],'upload')
        self.assertTrue(result['simulated_preparation_complete'])
        self.assertFalse(result['ready_for_human_portal'])
        sha=self.state()['snapshot']['package_sha256']
        self.answer('upload',self.portal_response('upload',package_sha256=sha))
        self.answer('portal-validation',self.portal_response('portal-validation',metadata_passed=True,skills_passed=True,mcp_passed=True,review_materials_checked=True))
        self.answer('submit-review',self.portal_response('submit-review'))
        waiting=self.answer('review-decision',self.portal_response('review-decision',decision='pending'))
        self.assertEqual(waiting['next']['id'],'review-decision')
        self.answer('publish',self.portal_response('publish',listing_url='https://fixture.invalid/plugin'),expected=2)
        self.answer('review-decision',self.portal_response('review-decision',decision='approved'))
        result=self.answer('publish',self.portal_response('publish',listing_url='https://fixture.invalid/plugin'))
        self.assertEqual(result['next']['title'],'Simulation complete')
        self.assertFalse(result['published']);self.assertFalse(result['submitted'])
        self.assertFalse(result['portal_actions_performed_by_tool'])

    def test_desktop_route_requests_allowlist_and_skips_remote_materials(self):
        result=self.start(FX/'desktop-stdio')
        self.assertEqual(result['next']['id'],'allowlist')
        result=self.answer('allowlist',json.loads((FX/'desktop-allowlist.json').read_text()))
        result=self.finish_preparation()
        ids={r['id'] for r in result['progress']}
        self.assertNotIn('review-materials',ids)
        self.assertIn('desktop-install',ids)

    def test_real_session_cannot_use_synthetic_host_coverage(self):
        target=self.root/'skills-target';target.mkdir()
        for name in ('plugin.json','.codex-plugin/plugin.json','skills/prepare-plugin-submission/SKILL.md'):
            # A minimal valid skills target, without the real package's linked resources.
            if name!='plugin.json':continue
            manifest=json.loads((FX/'desktop-stdio/plugin.json').read_text())
            manifest.pop('mcpServers',None)
            (target/name).write_text(json.dumps(manifest))
        shutil.copytree(FX/'desktop-stdio/assets',target/'assets')
        (target/'skills/example').mkdir(parents=True)
        (target/'skills/example/SKILL.md').write_text('---\nname: example\ndescription: Exercise a controlled fixture.\n---\nReturn the controlled result.\n')
        result=self.start(target,synthetic=False)
        self.assertEqual(result['next']['id'],'understanding')
        self.answer('test-plan',{'cases':self.plan_cases()})
        result=self.import_capture()
        self.assertEqual(result['next']['id'],'host-tests')
        self.assertTrue(all(r['status']=='Not run' for r in result['next']['coverage']))
        self.assertFalse(result['ready_for_human_portal'])

    def test_target_change_invalidates_reports_confirmations_and_portal_state(self):
        target=self.root/'desktop';shutil.copytree(FX/'desktop-stdio',target)
        self.start(target);self.answer('allowlist',json.loads((FX/'desktop-allowlist.json').read_text()))
        self.finish_preparation()
        self.answer('upload',self.portal_response('upload',package_sha256=self.state()['snapshot']['package_sha256']))
        old=self.state()['snapshot']['package_sha256']
        manifest=json.loads((target/'plugin.json').read_text());manifest['version']='0.1.1';(target/'plugin.json').write_text(json.dumps(manifest))
        result=self.run_cli('next','--session',self.session)
        self.assertNotEqual(result['next']['id'],'upload')
        self.assertNotEqual(self.state()['snapshot']['package_sha256'],old)
        self.assertFalse(self.state()['host_rows']);self.assertNotIn('upload',self.state()['answers'])
        self.assertTrue(any(e['kind']=='target-changed' for e in self.state()['history']))
        self.assertEqual(self.state()['answers']['hosts']['hosts'],['chatgpt'])

    def test_defer_host_tests_prepares_other_materials_without_skipping_gate(self):
        self.start(FX/'review-prep.zip');self.answer('test-plan',{'cases':self.plan_cases()})
        result=self.run_cli('defer','--session',self.session,'--reason','Host temporarily unavailable')
        self.assertEqual(result['next']['id'],'review-materials')
        self.assertFalse(result['ready_for_human_portal'])
        # A delayed capture remains importable while another preparation step is current.
        self.import_capture()
        self.assertTrue(self.state()['host_rows'])

    def test_remote_plan_cannot_drop_supplied_review_cases(self):
        self.start(FX/'review-prep.zip')
        self.answer('test-plan',{'cases':self.plan_cases()[:1]},expected=2)
        self.assertNotIn('test-plan',self.state()['answers'])

    def test_stale_report_and_optimistic_revision_are_rejected_without_advancing(self):
        self.start(FX/'review-prep.zip');self.answer('test-plan',{'cases':self.plan_cases()})
        before=self.session.read_bytes();self.import_capture(tamper=True)
        self.assertEqual(self.session.read_bytes(),before)
        self.run_cli('next','--session',self.session,'--expected-revision','-1',expected=2)
        self.assertEqual(self.session.read_bytes(),before)

    def test_resume_and_revisit_keep_intent_but_invalidate_affected_evidence(self):
        self.start(FX/'review-prep.zip');self.finish_preparation()
        self.run_cli('pause','--session',self.session)
        self.assertEqual(self.run_cli('next','--session',self.session)['next']['id'],'resume')
        self.assertEqual(self.run_cli('resume','--session',self.session)['next']['id'],'upload')
        result=self.run_cli('revisit','--session',self.session,'--step','test-plan')
        self.assertEqual(result['next']['id'],'test-plan');self.assertFalse(self.state()['host_rows'])
        self.assertEqual(self.state()['answers']['hosts']['hosts'],['chatgpt'])

    def test_portal_validation_failure_and_wrong_release_do_not_advance(self):
        self.start(FX/'review-prep.zip');self.finish_preparation()
        self.answer('upload',self.portal_response('upload',package_sha256='0'*64),expected=2)
        self.answer('upload',self.portal_response('upload',package_sha256=self.state()['snapshot']['package_sha256']))
        response=self.portal_response('portal-validation',metadata_passed=False,skills_passed=True,mcp_passed=True,review_materials_checked=True,issues=['Correct listing metadata'])
        result=self.answer('portal-validation',response)
        self.assertEqual(result['next']['id'],'portal-validation')
        self.assertEqual(result['next']['actor'],'assistant')
        self.assertIn('Correct listing metadata',result['next']['last_report']['issues'])
        response['release_reference']='unrelated-release';response['metadata_passed']=True
        self.answer('portal-validation',response,expected=2)

    def test_open_official_requirement_blocks_but_recommendation_can_remain_open(self):
        self.start(FX/'review-prep.zip');self.answer('test-plan',{'cases':self.plan_cases()});self.import_capture()
        self.answer('review-materials',{'recording_accessible':True,'reviewer_access_ready':True,'confirmed_by':'Fixture','reference':'synthetic:demo'})
        self.seed_finding()
        result=self.run_cli('next','--session',self.session)
        rows=[dict(id=r['id'],status='Not run',observed_result='Deliberately unresolved synthetic observation',evidence_reference='synthetic:pending') for r in result['next']['requirements']]
        result=self.answer('requirement-review',{'decisions':rows})
        self.assertEqual(result['next']['id'],'requirement-review')
        self.assertTrue(all(r['classification']=='official_requirement' for r in result['next']['requirements']))

    def test_executable_mode_is_preserved_and_only_one_product_skill_is_exposed(self):
        source=self.root/'desktop';shutil.copytree(FX/'desktop-stdio',source)
        (source/'server.js').chmod(0o755)
        self.start(source)
        with zipfile.ZipFile(self.state()['snapshot']['archive']) as archive:
            self.assertTrue((archive.getinfo('server.js').external_attr>>16)&0o111)
        self.assertEqual([p.relative_to(ROOT).as_posix() for p in ROOT.rglob('SKILL.md')],['skills/prepare-plugin-submission/SKILL.md'])

    def test_existing_audit_outputs_are_bound_to_the_attached_target(self):
        imported=self.root/'imported'
        subprocess.run([sys.executable,str(SCRIPTS/'prepare_workflow.py'),'audit','--source',str(FX/'review-prep.zip'),'--output',str(imported),'--synthetic'],check=True,capture_output=True)
        self.run_cli('start','--session',self.session,'--source',FX/'desktop-stdio',
                     '--goal','public-submission','--synthetic','--pack',imported,expected=2)
        self.assertFalse(self.session.exists())
        result=self.run_cli('start','--session',self.session,'--source',FX/'review-prep.zip',
                     '--goal','public-submission','--synthetic','--pack',imported)
        self.assertEqual(result['next']['id'],'understanding')

    def test_export_restore_resumes_after_paths_change_without_duplicating_questions(self):
        self.start(FX/'review-prep.zip');self.finish_preparation()
        bundle=self.root/'saved-session.zip'
        result=self.run_cli('export','--session',self.session,'--output',bundle)
        self.assertEqual(result['session_bundle'],str(bundle))
        old_workspace=self.session.with_name('session.files')
        shutil.rmtree(old_workspace);self.session.unlink()
        self.session=self.root/'different-directory/resumed.json'
        result=self.run_cli('restore','--session',self.session,'--bundle',bundle)
        self.assertEqual(result['next']['id'],'upload')
        self.assertTrue(Path(result['artifacts']['archive']).is_file())
        self.assertTrue(self.state()['host_rows'])
        self.assertFalse(result['published'])

    def test_cached_pass_flags_cannot_override_saved_capture_status(self):
        self.start(FX/'review-prep.zip');self.answer('test-plan',{'cases':self.plan_cases()})
        self.import_capture(status='Failed')
        state=self.state()
        for row in state['host_rows'].values(): row['status']='Passed'
        self.session.write_text(json.dumps(state))
        result=self.run_cli('next','--session',self.session,expected=2)
        self.assertIn('Cached host status disagrees',result['message'])

    def test_requirement_evidence_is_imported_and_checked_after_relocation(self):
        self.start(FX/'review-prep.zip');self.answer('test-plan',{'cases':self.plan_cases()});self.import_capture()
        self.answer('review-materials',{'recording_accessible':True,'reviewer_access_ready':True,'confirmed_by':'Fixture','reference':'synthetic:demo'})
        self.seed_finding('structural_check')
        result=self.run_cli('next','--session',self.session)
        evidence=self.root/'observations.json';evidence.write_text(json.dumps({'origin':'synthetic','observation':'Controlled importer regression only'}))
        sha=hashlib.sha256(evidence.read_bytes()).hexdigest()
        rows=[dict(id=r['id'],status='Passed',observed_result='Synthetic parser exercise, not actual integration verification',evidence_reference='Synthetic local observation',evidence={'file':evidence.name,'sha256':sha}) for r in result['next']['requirements']]
        result=self.answer('requirement-review',{'decisions':rows})
        self.assertEqual(result['next']['id'],'creator-facts')
        evidence.unlink()
        result=self.run_cli('next','--session',self.session)
        bundle=self.root/'evidence-session.zip';self.run_cli('export','--session',self.session,'--output',bundle)
        self.session=self.root/'relocated/session.json';self.run_cli('restore','--session',self.session,'--bundle',bundle)
        row=self.state()['answers']['requirement-review']['decisions'][0]
        path=Path(row['evidence']['file']);self.assertTrue(path.is_file())
        self.assertEqual(row['evidence_state'],'Imported artifact integrity checked')
        path.write_text('tampered')
        self.run_cli('next','--session',self.session,expected=2)


if __name__=='__main__': unittest.main()

