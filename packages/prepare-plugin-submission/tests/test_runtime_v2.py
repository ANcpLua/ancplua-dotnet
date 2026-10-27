"""Controlled source, HTTP, question and review fixtures; no portal or target execution."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'skills/prepare-plugin-submission/scripts'
FX=ROOT/'tests/fixtures'
sys.path.insert(0,str(SCRIPTS))
import audit_target
import check_package
import openai_core as policy
import wizard
import wizard_core as core


def doc(text,ident='review.errors',status='current'):
    row=dict(id=ident,url='https://developers.openai.com/plugins/deploy/submission-errors',
        role='primary',status=status,validated_at='2026-10-16T15:00:00+00:00',sha256=hashlib.sha256(text.encode()).hexdigest())
    row['sections']=policy.index_document(row,text)
    return row


class OfficialDocuments(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT.parent);self.addCleanup(self.temp.cleanup)
        self.work=Path(self.temp.name)
        self.registry=json.loads((SCRIPTS.parent/'references/official-docs-sources.json').read_text())

    def test_general_target_never_selects_specialized_specs(self):
        selected=policy.select_documents({'mcp':True,'skills':True},self.registry)
        self.assertFalse(any(s.get('requires_detected_activity') for s in selected))
        text='# General\nGeneral guidance.\n# Product checkout conversion spec\nMust not be active.\n# Restaurant reservation conversion spec\nAlso inactive.\n# Local services Get Quote\nNot applicable.\n'
        active=policy.active_export(text,{})
        self.assertIn('General guidance',active);self.assertNotIn('Must not be active',active)
        self.assertNotIn('Also inactive',active);self.assertNotIn('Not applicable',active)

    def test_detected_activity_selects_only_its_specialized_primary(self):
        for activity in ('local_services_quote','product_checkout','restaurant_reservation'):
            selected=policy.select_documents({activity:True},self.registry)
            self.assertEqual([s['when_any'][0] for s in selected if s['requires_detected_activity']],[activity])

    def test_stock_quotes_calendar_and_readme_mentions_do_not_detect_conversion(self):
        class C:settings={};servers={}
        files={'README.md':b'Quotes, product checkout and restaurant reservations are ideas.',
            'tools-list.json':json.dumps({'tools':[{'name':'get_stock_quote','description':'Stock price'},
                {'name':'create_calendar_event','description':'Book an appointment'}]}).encode()}
        detected=audit_target.source_details(files,C())['detected']
        self.assertFalse(any(detected[k] for k in ('local_services_quote','product_checkout','restaurant_reservation')))

    def test_source_tool_signature_detects_checkout(self):
        class C:settings={};servers={}
        tools={'tools':[dict(name='create_checkout_session',description='Create product checkout',inputSchema={'properties':{'line_items':{'type':'array'}}})]}
        d=audit_target.source_details({'tools-list.json':json.dumps(tools).encode()},C())
        self.assertTrue(d['detected']['product_checkout'])
        self.assertFalse(d['detected']['restaurant_reservation'])

    def test_primary_limit_overrides_old_export_and_handles_commas(self):
        current=doc('# Current\nDisplay name is required; at most 40 characters.\nLong description is required; at most 4,000 characters.')
        old=doc('Display name must be at most 10 characters.','export');old['role']='export'
        context=policy.policy_context([old,current])
        self.assertFalse(policy.policy_findings(context,{'displayName':'x'*35,'longDescription':'x'*3900}))
        findings=policy.policy_findings(context,{'displayName':'x'*41,'longDescription':'x'*4001})
        self.assertEqual({f['maximum'] for f in findings},{40,4000})
        self.assertTrue(all(f['source_sha256']==current['sha256'] for f in findings))

    def test_table_constraints_do_not_bind_an_incidental_field_mention(self):
        source=doc('| `name` | Required stable identifier, at most 12 characters. Keep it separate from the display name. |\n| `displayName` | Required; at most 40 characters. |')
        context=policy.policy_context([source]);self.assertEqual([r['maximum'] for r in context['constraints']],[40])
        self.assertFalse(policy.policy_findings(context,{'displayName':'x'*35}))

    def test_current_review_counts_allow_per_server_declarations(self):
        source=doc('Initial MCP review requires five positive and three negative cases.','publication.submission')
        context=policy.policy_context([source]);server=lambda n:{'url':'https://fixture.invalid/'+n,
            'extensions':{'com.openai':{'review':{'testCases':[{}]*5,'negativeTestCases':[{}]*3}}}}
        servers={n:server(n) for n in ('one','two')}
        self.assertFalse(policy.policy_findings(context,{},remote=True,servers=servers))
        servers['two']['extensions']['com.openai']['review']['testCases']=[]
        findings=policy.policy_findings(context,{},remote=True,servers=servers)
        self.assertEqual(len(findings),1);self.assertEqual(findings[0]['path'],'mcpServers.two.review.positive')

    def test_advice_cannot_be_promoted_to_official_requirement(self):
        source=doc('Display name should be at most 20 characters.')
        context=policy.policy_context([source]);findings=policy.policy_findings(context,{'displayName':'x'*30})
        self.assertEqual(findings[0]['severity'],'warning')
        rule=dict(source_id=source['id'],source_sha256=source['sha256'],quote=source['sections'][0]['text'],classification='official_requirement')
        with self.assertRaises(ValueError):policy.validate_rule(rule,[source])

    def test_rule_needs_current_exact_primary_span(self):
        source=doc('Display name must be at most 40 characters.')
        rule=dict(source_id=source['id'],source_sha256=source['sha256'],quote=source['sections'][0]['text'],classification='official_requirement')
        self.assertEqual(policy.validate_rule(rule,[source])['id'],source['id'])
        with self.assertRaises(ValueError):policy.validate_rule(dict(rule,source_sha256='0'*64),[source])
        with self.assertRaises(ValueError):policy.validate_rule(dict(rule,quote='A rule that does not exist here.'),[source])
        with self.assertRaises(ValueError):policy.validate_rule(rule,[dict(source,status='cached-unverified')])

    def test_primary_imperatives_and_prohibitions_do_not_need_a_magic_verb(self):
        for quote in ('For public plugin submission, deploy the MCP server at a stable HTTPS endpoint.',
                      'Trial or demo plugins will not be accepted.',
                      'Do not append Plugin to a product name.'):
            source=doc(quote)
            rule=dict(source_id=source['id'],source_sha256=source['sha256'],quote=quote,classification='official_requirement')
            self.assertEqual(policy.validate_rule(rule,[source])['sha256'],source['sha256'])

    def test_html_navigation_is_not_policy_text(self):
        text=policy.article_text('<html><nav>Irrelevant rule</nav><main><h1>Policy</h1><p>Useful content.</p><script>fake requirement</script></main><footer>Other links</footer></html>')
        self.assertIn('# Policy',text);self.assertIn('Useful content',text)
        self.assertNotIn('Irrelevant',text);self.assertNotIn('fake',text);self.assertNotIn('Other',text)

    def test_moved_page_and_new_index_page_are_discovered(self):
        registry={'sources':[dict(id='packaging',primary_url='https://developers.openai.com/plugins/old',title='Package your plugin',when_any=['always'])]}
        index='[Package your plugin](https://developers.openai.com/plugins/build/plugins.md)\n[New general guidance](https://developers.openai.com/plugins/guides/new-page.md)'
        selected=policy.select_documents({},registry,index)
        self.assertEqual(selected[0]['primary_url'],'https://developers.openai.com/plugins/build/plugins')
        self.assertIn('https://developers.openai.com/plugins/guides/new-page',{s['primary_url'] for s in selected})

    def test_live_sync_requests_only_applicable_pages_and_indexes_them(self):
        state=core.new_session('fixture','2026-10-16T15:00:00+00:00',True);state['snapshot']={'features':{'skills':True}}
        called=[]
        def fetch(url,before):
            called.append(url)
            text='[Skills](https://developers.openai.com/plugins/concepts/skills.md)' if url.endswith('llms.txt') else '# Skills\nUse the supported skill workflow.'
            return dict(status=200,url=url,body=text.encode(),etag='fixture')
        result=wizard.sync_documents(state,self.work,fetch=fetch)
        self.assertFalse(any('conversion-spec' in u for u in called))
        records=wizard.document_records(result,self.work)
        self.assertTrue(all(d['status']=='current' for d in records))
        self.assertTrue(policy.search_documents(records,'supported workflow'))

    def test_304_revalidates_exact_cached_body_and_failure_does_not_invent_a_rule(self):
        state=core.new_session('fixture','2026-10-16T15:00:00+00:00',True);state['snapshot']={'features':{}}
        def initial(url,before):return dict(status=200,url=url,body=b'# General\nCurrent useful source.',etag='fixture')
        first=wizard.sync_documents(state,self.work,fetch=initial)
        def retained(url,before):
            self.assertEqual(before['etag'],'fixture');return dict(status=304,url=url,body=b'')
        second=wizard.sync_documents(first,self.work,fetch=retained)
        self.assertEqual(first['docs']['content_sha256'],second['docs']['content_sha256'])
        def missing(url,before):raise ValueError('Controlled network outage')
        offline=wizard.sync_documents(second,self.work,fetch=missing)
        self.assertTrue(offline['docs']['gaps'])
        self.assertTrue(all(d['status']=='cached-unverified' for d in offline['docs']['documents']))
        self.assertFalse(policy.rule_candidates(wizard.document_records(offline,self.work)))

    def test_foreign_documentation_url_is_rejected(self):
        self.assertFalse(policy.official_url('https://example.com/plugins/rules'))
        self.assertFalse(policy.official_url('https://developers.openai.com.evil.example/plugins/rules'))
        with self.assertRaises(ValueError):wizard.fetch_url('https://example.com/rules')


class RuntimeV2(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=ROOT.parent);self.addCleanup(self.temp.cleanup)
        self.work=Path(self.temp.name);self.session=self.work/'session.json';self.input=self.work/'input.json'

    def cli(self,*args,expected=0):
        run=subprocess.run([sys.executable,str(SCRIPTS/'wizard.py'),*map(str,args)],capture_output=True,text=True,
            env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
        self.assertEqual(run.returncode,expected,run.stdout+run.stderr)
        return json.loads(run.stdout or run.stderr)

    def start(self,source=None,*extra):
        return self.cli('start','--session',self.session,'--source',source or FX/'review-prep.zip','--synthetic','--docs-mode','offline',*extra)

    def state(self):return json.loads(self.session.read_text())

    def choose(self,selected,**extra):
        q=self.state()['question_plan'];value=dict(question_id=q['id'],revision=q['revision'],selected=selected,**extra)
        self.input.write_text(json.dumps(value));return self.cli('choose','--session',self.session,'--input',self.input)

    def unavailable(self):
        state=self.state();job=state['jobs']['independent-review']
        value=dict(status='Unavailable',reason='Controlled fixture has no actual host agent',binding=core.binding(state),
            docs_sha256=state['docs']['content_sha256'],request_sha256=job['request_sha256'])
        self.input.write_text(json.dumps(value));return self.cli('review','--session',self.session,'--input',self.input)

    def host_capture(self):
        state=self.state();plan=json.loads(Path(state['artifacts']['plan']).read_text());folder=self.work/'host';folder.mkdir(exist_ok=True)
        rows=[]
        for n,case in enumerate(plan['host_cases']):
            capture=dict(binding=plan['binding'],package_sha256=plan['package_sha256'],host='chatgpt',origin='synthetic',case_id=case['id'],status='Passed',
                expected=case['expected'],observed='Controlled synthetic observation',assessment_rationale='Contract fixture only',tool_calls=[],side_effects={'expected':'none','observed':'none'})
            path=folder/(str(n)+'.json');path.write_text(json.dumps(capture));rows.append(dict(id=case['id'],status='Passed',expected=case['expected'],evidence={'file':path.name,'sha256':wizard.file_sha(path)}))
        report=dict(schema_version=1,report_kind='product-host',host='chatgpt',origin='synthetic',binding=plan['binding'],package_sha256=plan['package_sha256'],
            observer='Controlled fixture',observed_at='2026-10-16T15:00:00Z',environment={'host_version':'synthetic','runner_version':'test'},cases=rows)
        path=folder/'report.json';path.write_text(json.dumps(report));return self.cli('ingest','--session',self.session,'--report',path)

    def report(self,findings=None,**overrides):
        state=self.state();job=state['jobs']['independent-review'];raw=self.work/'raw-agent.txt';raw.write_text('Controlled agent-output fixture; not an actual model run.')
        value=dict(binding=core.binding(state),docs_sha256=state['docs']['content_sha256'],request_sha256=job['request_sha256'],
            reviewer_id='controlled-second-agent',provider='unit-test fixture',origin='synthetic',summary='Controlled observation',findings=findings or [],
            evidence=dict(file=raw.name,sha256=wizard.file_sha(raw)),**overrides)
        return value

    def test_one_native_acceptance_generates_cases_and_same_source_claims(self):
        result=self.start();self.assertEqual(result['next']['id'],'understanding')
        widget=result['native_widget']['ask_user_input']['questions'][0]
        self.assertEqual(set(widget),{'question','options','type','free_text_placeholder'})
        self.assertEqual(widget['options'][0],'Use suggested setup');self.assertEqual(widget['type'],'single_select')
        result=self.choose(['Use suggested setup']);state=self.state()
        self.assertEqual(result['next']['id'],'independent-review');self.assertTrue(state['choices']['confirmed'])
        self.assertGreater(len(state['answers']['test-plan']['cases']),8)
        pack=Path(state['artifacts']['pack'])
        self.assertTrue((pack/'submission/reviewer-notes.md').exists())
        self.assertEqual(json.loads((pack/'submission/choices.json').read_text())['choices'],state['choices'])
        self.assertFalse(result['published'])

    def test_question_is_stable_across_read_and_stale_replay_is_rejected(self):
        first=self.start();q=first['question_plan']
        second=self.cli('next','--session',self.session);self.assertEqual(q,second['question_plan'])
        self.choose(['accept']);before=self.session.read_bytes()
        self.input.write_text(json.dumps(dict(question_id=q['id'],revision=q['revision'],selected=['accept'])))
        self.cli('choose','--session',self.session,'--input',self.input,expected=2)
        self.assertEqual(self.session.read_bytes(),before)

    def test_multiselect_adjustment_drives_generated_cases(self):
        self.start();self.choose(['boundaries']);q=self.state()['question_plan']
        self.assertEqual(q['payload']['ask_user_input']['questions'][0]['type'],'multi_select')
        self.choose(['unrelated']);self.choose(['accept']);state=self.state()
        negative=[c for c in state['answers']['test-plan']['cases'] if c['kind']=='negative' and c['id'].startswith('boundary:')]
        self.assertEqual([c['id'] for c in negative],['boundary:unrelated'])

    def test_private_audience_does_not_enter_public_portal_flow(self):
        self.start();self.choose(['audience']);result=self.choose(['private'])
        self.assertEqual(result['next']['id'],'done');self.assertEqual(self.state()['choices']['audience'],'private')
        self.assertFalse(result['ready_for_human_portal']);self.assertFalse(result['published'])

    def test_optional_correction_becomes_agent_work_not_ignored_acceptance(self):
        self.start();result=self.choose(['accept'],correction='Focus the description on source inspection only.')
        self.assertFalse(self.state()['choices']['confirmed']);self.assertEqual(result['next']['id'],'refine-understanding')
        state=self.state();draft=copy.deepcopy(state['understanding']);draft['summary']='Inspect source only.'
        self.input.write_text(json.dumps(dict(content_sha256=state['snapshot']['content_sha256'],provider='controlled synthesis',draft=draft)))
        result=self.cli('refine','--session',self.session,'--input',self.input)
        self.assertEqual(result['next']['draft']['summary'],'Inspect source only.')
        self.assertNotIn('pending_correction',self.state())

    def test_synthesis_rejects_nonexistent_source_reference(self):
        self.start();s=self.state();draft=copy.deepcopy(s['understanding']);draft['tasks'][0]['source_paths']=['imaginary.py']
        self.input.write_text(json.dumps(dict(content_sha256=s['snapshot']['content_sha256'],provider='fixture',draft=draft)))
        self.cli('refine','--session',self.session,'--input',self.input,expected=2)

    def test_refined_question_survives_observation_before_its_answer(self):
        self.start();state=self.state();draft=copy.deepcopy(state['understanding'])
        draft['summary']='Report the status of a supplied record.'
        draft['tasks'][0]['expected']='Report the supplied status without claiming a remote lookup.'
        self.input.write_text(json.dumps(dict(content_sha256=state['snapshot']['content_sha256'],provider='controlled synthesis',draft=draft)))
        refined=self.cli('refine','--session',self.session,'--input',self.input)
        refreshed=self.cli('next','--session',self.session)
        self.assertEqual(refined['question_plan'],refreshed['question_plan'])
        normalized=copy.deepcopy(self.state()['understanding'])
        self.choose(['accept']);self.assertEqual(self.state()['understanding'],normalized)
        self.assertEqual(normalized['summary'],draft['summary'])
        self.assertTrue(self.state()['choices']['confirmed'])

    def test_monorepo_asks_only_which_observed_plugin_root(self):
        folder=self.work/'monorepo'
        with zipfile.ZipFile(FX/'review-prep.zip') as z:
            for root in ('one','two'):
                for name in z.namelist():
                    if name.endswith('/'):continue
                    p=folder/root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
        result=self.start(folder);self.assertEqual(result['next']['id'],'plugin-root')
        self.assertEqual([o['id'] for o in result['question_plan']['options']],['one','two'])
        result=self.choose(['two']);self.assertEqual(result['next']['id'],'understanding')
        self.assertEqual(self.state()['source_origin']['plugin_root'],'two')

    def test_github_acquisition_pins_public_and_private_sources(self):
        body=(FX/'review-prep.zip').read_bytes();commit='a'*40
        for private in (False,True):
            folder=self.work/str(private);folder.mkdir()
            def fetch(url,previous=None,github=False):
                if '/commits/' in url:payload=json.dumps({'sha':commit}).encode()
                elif '/zipball/' in url:payload=body
                else:payload=json.dumps({'default_branch':'main','private':private}).encode()
                return dict(status=200,url=url,body=payload)
            with patch.object(wizard,'fetch_url',fetch):
                acquired=wizard.acquire_source('https://github.com/fixture/integration',folder)
            self.assertEqual(acquired['origin']['commit'],commit)
            self.assertEqual(acquired['origin']['visibility'],'private' if private else 'public')
            self.assertEqual(check_package.load_files(Path(acquired['path'])),check_package.load_files(FX/'review-prep.zip'))

    def test_many_plugin_roots_fit_native_options_and_can_be_selected(self):
        folder=self.work/'monorepo';manifest=check_package.load_files(FX/'review-prep.zip')['plugin.json']
        for n in range(21):
            path=folder/('p'+str(n).zfill(2))/'plugin.json';path.parent.mkdir(parents=True);path.write_bytes(manifest)
        result=self.start(folder);self.assertLessEqual(len(result['question_plan']['options']),10)
        result=self.choose(['/next']);self.assertLessEqual(len(result['question_plan']['options']),10)
        self.assertIn('p08',[o['id'] for o in result['question_plan']['options']])
        self.choose(['/previous']);self.choose(['/next']);self.choose(['/next'])
        self.choose(['p20']);self.assertEqual(self.state()['source_origin']['plugin_root'],'p20')

    def test_wrapped_monorepo_and_repair_preserve_executable_permissions(self):
        source=self.work/'wrapped.zip'
        with zipfile.ZipFile(source,'w') as archive:
            for root in ('one','two'):
                for name,data in check_package.load_files(FX/'review-prep.zip').items():
                    archive.writestr('repo/'+root+'/'+name,data)
                entry=zipfile.ZipInfo('repo/'+root+'/scripts/run.sh');entry.external_attr=0o100755<<16
                archive.writestr(entry,b'#!/bin/sh\nexit 0\n')
        self.start(source);self.choose(['two']);state=self.state()
        self.assertTrue(check_package.load_files(Path(state['snapshot']['archive'])).modes['scripts/run.sh']&0o111)
        value=dict(content_sha256=state['snapshot']['content_sha256'],changes=[dict(path='scripts/run.sh',
            before_sha256=hashlib.sha256(b'#!/bin/sh\nexit 0\n').hexdigest(),replacement='#!/bin/sh\nexit 1\n')])
        self.input.write_text(json.dumps(value));self.cli('apply-fix','--session',self.session,'--input',self.input)
        self.assertTrue(check_package.load_files(Path(self.state()['snapshot']['archive'])).modes['scripts/run.sh']&0o111)

    def test_malformed_optional_eval_json_does_not_abort_source_inspection(self):
        folder=self.work/'target';folder.mkdir()
        for name,data in check_package.load_files(FX/'review-prep.zip').items():
            path=folder/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        path=folder/'evals/cases.json';path.parent.mkdir();path.write_text('{broken')
        self.start(folder);self.assertEqual(self.state()['snapshot']['facts']['audit_observation']['json_eval_cases'],0)

    def test_independent_review_requires_raw_output_distinct_actor_and_current_binding(self):
        self.start();self.choose(['accept']);value=self.report();self.input.write_text(json.dumps(value))
        result=self.cli('review','--session',self.session,'--input',self.input)
        self.assertEqual(result['next']['id'],'host-tests');self.assertFalse(result['independent_review_verified'])
        state=self.state();Path(state['jobs']['independent-review']['evidence']).write_text('tampered')
        self.cli('next','--session',self.session,expected=2)

    def test_same_agent_cannot_pass_as_independent(self):
        self.start();self.choose(['accept']);value=self.report();value['reviewer_id']=self.state()['actor_id']
        self.input.write_text(json.dumps(value));self.cli('review','--session',self.session,'--input',self.input,expected=2)

    def test_dispatched_job_receipt_resumes_without_a_completed_verdict(self):
        self.start();self.choose(['accept']);s=self.state();job=s['jobs']['independent-review']
        receipt=dict(status='Running',binding=core.binding(s),docs_sha256=s['docs']['content_sha256'],request_sha256=job['request_sha256'],
            provider='controlled job fixture',job_reference='fixture-job-42',dispatched_at='2026-10-16T15:00:00Z')
        self.input.write_text(json.dumps(receipt));result=self.cli('review','--session',self.session,'--input',self.input)
        self.assertEqual(result['pending_jobs'][0]['job_reference'],'fixture-job-42');self.assertFalse(result['independent_review_verified'])
        bundle=self.work/'running.zip';self.cli('export','--session',self.session,'--output',bundle)
        self.session=self.work/'restored/session.json';result=self.cli('restore','--session',self.session,'--bundle',bundle)
        self.assertEqual(result['next']['job']['status'],'Running');self.assertEqual(result['next']['job']['job_reference'],'fixture-job-42')

    def test_official_guidance_without_a_primary_span_is_rejected(self):
        self.start();self.choose(['accept'])
        finding=dict(id='unproven',classification='official_guidance',source_path='plugin.json',message='Unattributed advice',fix='Inspect source')
        self.input.write_text(json.dumps(self.report([finding])))
        self.cli('review','--session',self.session,'--input',self.input,expected=2)

    def test_concrete_independent_finding_precedes_host_execution(self):
        self.start();self.choose(['accept'])
        finding=dict(id='mismatch',classification='structural_check',source_path='plugin.json',message='Observed declaration mismatch',fix='Align the declarations')
        self.input.write_text(json.dumps(self.report([finding])))
        result=self.cli('review','--session',self.session,'--input',self.input)
        self.assertEqual(result['next']['id'],'requirement-review')
        self.assertEqual(result['next']['requirements'][0]['id'],'mismatch')

    def test_changed_document_invalidates_review_but_preserves_host_capture(self):
        self.start();self.choose(['accept']);self.unavailable();self.host_capture();before=self.state()['host_rows']
        self.input.write_text(json.dumps({'origin':'observed','documents':[dict(url='https://developers.openai.com/plugins/plan/use-case',
            text='# Controlled changed page\nSupported tasks should have useful outcomes.',provider='unit-test document fixture',observed_at='2026-10-16T15:10:00+00:00')]}))
        self.cli('sync-docs','--session',self.session,'--input',self.input)
        self.assertEqual(self.state()['host_rows'],before)
        self.assertEqual(self.state()['jobs']['independent-review']['status'],'Pending')

    def test_changed_plan_invalidates_old_review_before_reusing_its_verdict(self):
        self.start();self.choose(['accept']);self.input.write_text(json.dumps(self.report()))
        self.cli('review','--session',self.session,'--input',self.input);old=self.state()['jobs']['independent-review']
        self.cli('revisit','--session',self.session,'--step','test-plan')
        cases=core.derive_test_plan(self.state());cases[0]['expected']='A more precise expected fixture result.'
        self.input.write_text(json.dumps({'cases':cases}))
        result=self.cli('answer','--session',self.session,'--step','test-plan','--input',self.input)
        fresh=self.state()['jobs']['independent-review']
        self.assertEqual(result['next']['id'],'independent-review');self.assertEqual(fresh['status'],'Pending')
        self.assertNotEqual(fresh['request_sha256'],old['request_sha256'])

    def test_runner_adapter_executes_separate_controlled_process_and_copies_raw_output(self):
        self.start();self.choose(['accept']);runner=self.work/'runner.json'
        code='import json,sys; request=json.load(sys.stdin); print(json.dumps(dict(origin="synthetic",summary="Controlled process fixture",findings=[])))'
        runner.write_text(json.dumps([sys.executable,'-c',code]))
        result=self.cli('run-review','--session',self.session,'--runner',runner)
        self.assertEqual(result['next']['id'],'host-tests')
        self.assertTrue(Path(self.state()['jobs']['independent-review']['evidence']).is_file())

    def test_prepared_native_fix_repairs_real_reference_error_and_rechecks(self):
        folder=self.work/'target'
        with zipfile.ZipFile(FX/'review-prep.zip') as z:
            for name in z.namelist():
                if name.endswith('/'):continue
                path=folder/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(name))
        skill=folder/'skills/review-fixture/SKILL.md';good=skill.read_text();skill.write_text(good+'\n[Missing](missing.md)\n')
        result=self.start(folder);self.assertEqual(result['next']['id'],'package');s=self.state()
        fix=dict(content_sha256=s['snapshot']['content_sha256'],summary='Repair the missing skill reference',changes=[dict(path='skills/review-fixture/SKILL.md',before_sha256=wizard.file_sha(skill),replacement=good)])
        self.input.write_text(json.dumps(fix));self.cli('propose-fix','--session',self.session,'--input',self.input)
        result=self.choose(['apply']);self.assertEqual(result['next']['id'],'understanding')
        self.assertNotIn('Missing',check_package.load_files(Path(self.state()['snapshot']['archive']))['skills/review-fixture/SKILL.md'].decode())
        self.assertIn('Missing',skill.read_text())

    def test_export_restore_preserves_source_docs_choices_review_and_questions(self):
        self.start();self.choose(['accept']);self.input.write_text(json.dumps(self.report()));self.cli('review','--session',self.session,'--input',self.input)
        bundle=self.work/'checkpoint.zip';before=self.state();self.cli('export','--session',self.session,'--output',bundle)
        self.session=self.work/'new-location/restored.json';result=self.cli('restore','--session',self.session,'--bundle',bundle)
        state=self.state();self.assertEqual(state['choices'],before['choices']);self.assertEqual(state['snapshot']['package_sha256'],before['snapshot']['package_sha256'])
        self.assertEqual(state['docs']['content_sha256'],before['docs']['content_sha256']);self.assertTrue(Path(state['jobs']['independent-review']['evidence']).is_file())
        self.assertFalse(result['published']);self.assertTrue(Path(state['artifacts']['archive']).is_file())

    def test_version_one_migration_preserves_history_without_inventing_confirmation(self):
        s=core.new_session('old','2026-10-16T12:00:00+00:00',True);s['schema_version']=1
        for key in ('docs','choices','understanding','jobs','source_origin','question_plan'):s.pop(key,None)
        s['answers']['test-plan']={'cases':[{'id':'old-case','prompt':'Old task','expected':'Old result'}]}
        s['history']=[dict(kind='historical',detail={},at=s['created_at'],binding={},origin='fixture')]
        migrated=core.migrate(s,'2026-10-16T15:00:00+00:00')
        self.assertEqual(migrated['schema_version'],2);self.assertFalse(migrated['choices']['confirmed'])
        self.assertTrue(migrated['choices']['legacy_retained']);self.assertEqual(migrated['history'][0]['kind'],'historical')

    def test_actual_version_one_checkpoint_restores_and_retains_its_plan(self):
        fixture=ROOT/'evals/evidence/2.2.0/independent-wizard-evidence.zip'
        with zipfile.ZipFile(fixture) as archive:body=archive.read('submission-checkpoint.zip')
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            old=json.loads(archive.read('session.json'))['state']
        path=self.work/'v1.zip';path.write_bytes(body)
        result=self.cli('restore','--session',self.session,'--bundle',path)
        state=self.state();self.assertEqual(state['schema_version'],2)
        self.assertEqual(state['answers']['test-plan'],old['answers']['test-plan'])
        self.assertTrue(state['understanding']['tasks']);self.assertFalse(state['choices']['confirmed'])
        self.assertTrue(state['choices']['legacy_retained']);self.assertEqual(state['paused'],old['paused'])
        self.assertEqual(state['artifacts']['binding'],old['artifacts']['binding'])
        self.assertFalse(result['published']);self.assertFalse(result['current_policy_retrieved'])
        result=self.cli('resume','--session',self.session)
        self.assertEqual(result['next']['id'],'independent-review')


if __name__=='__main__':unittest.main()
