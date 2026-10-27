"""Pure guided-submission decisions. I/O and external actions belong to the host."""
import copy
import hashlib
import json
from datetime import datetime
from urllib.parse import urlsplit

SUBMISSION = 'https://developers.openai.com/plugins/deploy/submission'
DESKTOP = 'https://developers.openai.com/plugins/deploy/desktop-only'
TESTING = 'https://developers.openai.com/plugins/deploy/connect-chatgpt'
ORDER = ['source', 'goal', 'allowlist', 'package', 'understanding', 'independent-review', 'hosts', 'test-plan', 'host-tests',
         'review-materials', 'desktop-install', 'requirement-review', 'creator-facts', 'upload',
         'portal-validation', 'submit-review', 'review-decision', 'publish']
DEFERABLE = {'independent-review','host-tests', 'review-materials', 'desktop-install', 'requirement-review', 'creator-facts'}
HUMAN = {'review-materials', 'desktop-install', 'creator-facts', 'upload',
         'portal-validation', 'submit-review', 'review-decision', 'publish'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def new_session(session_id, now, synthetic=False, goal=None, hosts=None):
    state = dict(schema_version=2, session_id=session_id, revision=0, created_at=now,
                 updated_at=now, synthetic=synthetic, paused=False, source_path=None,
                 snapshot=None, answers={}, host_rows={}, deferred={}, artifacts={}, history=[],
                 source_origin={},source_pending=None,docs={},understanding=None,choices={},
                 question_plan=None,jobs={},findings=[],actor_id='host-primary',docs_mode='offline' if synthetic else 'live')
    if goal:
        validate_answer(state, 'goal', {'goal': goal})
        state['answers']['goal'] = {'goal': goal}
    if hosts:
        validate_answer(state, 'hosts', {'hosts': hosts})
        state['answers']['hosts'] = {'hosts': hosts}
    return state


def migrate(state, now):
    if state.get('schema_version') not in (1,2): raise ValueError('Unsupported session schema')
    state=copy.deepcopy(state)
    if state['schema_version']==1:
        for key,value in new_session(state['session_id'],now,state['synthetic']).items():
            state.setdefault(key,value)
        state['schema_version']=2
        state['choices']={'legacy_retained':bool(state['answers'].get('test-plan')),'confirmed':False}
        state['legacy_binding']=copy.deepcopy(state.get('artifacts',{}).get('binding'))
        state=event(state,'session-migrated',{'from':1,'retained_history':True,'creator_confirmation_invented':False},now)
    return state


def meaning(draft):
    return digest({k:draft.get(k) for k in ('summary','personas','tasks','boundaries','claims','data_access')}) if draft else None


def binding(state):
    snapshot = state.get('snapshot') or {}
    return dict(content_sha256=snapshot.get('content_sha256'), package_sha256=snapshot.get('package_sha256'),
                hosts=state['answers'].get('hosts', {}).get('hosts', []),
                test_plan_sha256=digest(state['answers'].get('test-plan', {})))


def event(state, kind, detail, now):
    state['history'].append(dict(kind=kind, detail=copy.deepcopy(detail), at=now,
                                 binding=binding(state), origin='synthetic' if state['synthetic'] else 'external claim or local workflow event'))
    state['revision'] += 1
    state['updated_at'] = now
    return state


def with_snapshot(state, snapshot, source_path, now):
    state = copy.deepcopy(state)
    old = state.get('snapshot')
    changed = old and any(old.get(k) != snapshot.get(k) for k in ('content_sha256', 'package_sha256'))
    if old and not changed:
        state['snapshot']=copy.deepcopy(snapshot);state['source_path']=source_path
        if not state.get('understanding'):
            state['understanding']=copy.deepcopy(snapshot['facts'].get('understanding_draft'))
        return state
    if changed:
        event(state, 'target-changed', {'previous': binding(state), 'invalidated': list(state['answers']),
                                      'previous_artifacts': state['artifacts']}, now)
        state['answers'] = {k: v for k, v in state['answers'].items() if k in ('goal', 'hosts')}
        state.update(host_rows={}, deferred={}, artifacts={})
        state['jobs']={};state['findings']=[];state.pop('legacy_binding',None)
        state.pop('proposed_fix',None)
        state['notice'] = 'The target changed. Earlier evidence and portal observations remain in history; current checks must be repeated.'
    override=state.get('draft_override',{})
    draft=override['draft'] if override.get('content_sha256')==snapshot['content_sha256'] else snapshot['facts'].get('understanding_draft')
    old_draft=state.get('understanding')
    if draft:
        if old_draft and meaning(old_draft)==meaning(draft):
            pass  # Provenance changed; confirmed product meaning did not.
        elif not state.get('choices',{}).get('legacy_retained'):
            state['choices']={};state['question_plan']=None
        state['understanding']=copy.deepcopy(draft)
    state['snapshot'] = copy.deepcopy(snapshot)
    state['source_path'] = source_path
    return event(state, 'target-inspected', {'content_sha256': snapshot['content_sha256'],
                                           'package_sha256': snapshot['package_sha256']}, now)


def host_coverage(state):
    rows = []
    for host in state['answers'].get('hosts', {}).get('hosts', []):
        for case in state['answers'].get('test-plan', {}).get('cases', []):
            found = state['host_rows'].get(host + ':' + case['id'], {})
            passed = (found.get('status') == 'Passed' and
                      (state['synthetic'] or found.get('origin') == 'observed'))
            status = 'Passed' if passed else 'Not run' if found.get('status') == 'Passed' else found.get('status', 'Not run')
            rows.append(dict(host=host, case_id=case['id'], status=status, reported_status=found.get('status', 'Not run'),
                             satisfies_gate=passed, origin=found.get('origin', 'missing')))
    return rows


def _confirmed(value, fields=('confirmed',)):
    return all(value.get(k) is True for k in fields) and all(nonempty(value.get(k)) for k in ('confirmed_by', 'reference'))


def requirement_gaps(state):
    if state.get('schema_version')==2:
        return [copy.deepcopy(f) for f in state.get('findings',[]) if f.get('severity') in ('error','hold') and f.get('status')=='Failed']
    facts = state['snapshot']['facts']
    decisions = {r['id']: r for r in state['answers'].get('requirement-review', {}).get('decisions', [])}
    gaps = []
    for req in facts['requirement_catalog']:
        original = facts['requirement_results'][req['id']]
        if original['status'] in ('Passed', 'Not applicable'):
            continue
        decision = decisions.get(req['id'])
        resolved = decision and decision['status'] in ('Passed', 'Not applicable') and decision.get('evidence_state') in ('Imported artifact integrity checked', 'Frozen source digest checked')
        if decision is None or (req['classification'] == 'official_requirement' and not resolved):
            gaps.append(dict(id=req['id'], summary=req['summary'], classification=req['classification'],
                             scope=req['scope'], source_url=req['source_url'],
                             observation=original['observed_result'], decision=decision))
    return gaps


def _card(step, title, actor, instruction, question=None, **extra):
    return dict(id=step, title=title, actor=actor, instruction=instruction, question=question, **extra)


def _preparation(state):
    a = state['answers']; snapshot = state['snapshot']; features = snapshot['features']
    report = snapshot['package_report']; public = a['goal']['goal'] == 'public-submission'
    blockers = [i for i in report['issues'] if i['severity'] in ('error', 'hold')]
    cards = []
    if public and features['local_mcp'] and any(d.get('id')=='publication.desktop' and d.get('status')=='current' for d in state.get('docs',{}).get('documents',[])):
        cards.append(((report.get('desktop_allowlist') or {}).get('record_accepted') is True,
            _card('allowlist', 'Confirm the desktop partner route', 'human',
                  'Use the submitting organization’s actual OpenAI confirmation. I will validate the record and rerun this route; it does not independently verify membership.',
                  'Has your OpenAI representative confirmed this organization’s local MCP allowlisting?', source_url=DESKTOP)))
    cards.append((not blockers, _card('package', 'Repair and recheck the package', 'assistant',
        'Inspect the first finding, make authorized source changes, refresh the target and rerun checks. Preserve the other findings until resolved.',
        findings=blockers, source_url=SUBMISSION)))
    if not public:
        return cards
    if state.get('pending_correction'):
        cards.append((False,_card('refine-understanding','Apply the creator correction','assistant',
            'Inspect the correction and update the source-backed draft through the refinement adapter before asking another choice.',correction=state['pending_correction'])))
    cards.append((state.get('choices',{}).get('confirmed') or state.get('choices',{}).get('legacy_retained'),
        _card('understanding','Confirm the suggested setup','human',
            'I drafted the tasks, ordinary boundaries and test prompts from the source. Accept the setup or adjust only what differs.',
            'Use this suggested setup for the submission?', draft=state.get('understanding'))))
    job=state.get('jobs',{}).get('independent-review',{})
    if not state.get('plan_editing'):
        cards.append((job.get('status') in ('Completed','Unavailable'),
            _card('independent-review','Check the source independently','assistant',
                'Resume the saved dispatched job and import its actual report. Continue other preparation while it runs.' if job.get('status')=='Running' else
                'Dispatch the saved independent-review request through a fresh host agent or a configured runner. Import its actual report. Continue other preparation while it runs.',
                job=job, completion_status='Unavailable' if job.get('status')=='Unavailable' else 'Completed')))
    gaps = requirement_gaps(state)
    cards.append((not gaps, _card('requirement-review', 'Resolve the applicable audit findings', 'assistant',
        'Inspect the actual target and current supporting source, apply the next actionable repair and recheck. Record evidence or resolve an inapplicable finding without adding submission rules.',
        requirements=gaps, artifacts=state['artifacts'])))
    cards += [
        (bool(a.get('hosts')), _card('hosts', 'Choose the intended hosts', 'human',
            'Reuse an explicitly selected host. Ask only if the intended availability is unknown.',
            'Will this plugin be available in ChatGPT, Codex, or both?', choices=['ChatGPT', 'Codex', 'Both'])),
        (bool(a.get('test-plan', {}).get('cases')), _card('test-plan', 'Prepare realistic test cases', 'assistant',
            'Derive prompts and independent expected results from the actual source and use cases. Reuse applicable review definitions. Ask only for behavior that source and prior answers do not establish.',
            supplied_review_cases=snapshot.get('review_cases', []), source_url=TESTING)),
    ]
    coverage = host_coverage(state)
    cards.append((bool(coverage) and all(r['satisfies_gate'] for r in coverage),
        _card('host-tests', 'Run the cases in the intended hosts', 'assistant',
              'Use available authorized host tools and capture actual behavior. If the creator must run a host step, give one prompt and the expected observation, then ingest the captured report. Synthetic evidence never verifies a real host.',
              question='Can we run the next missing case in the selected host, or should I continue the other preparation first?',
              coverage=coverage, artifacts=state['artifacts'], source_url=TESTING)))
    if features['remote_mcp']:
        cards.append((_confirmed(a.get('review-materials', {}), ('recording_accessible', 'reviewer_access_ready')),
            _card('review-materials', 'Rehearse the review handoff', 'human',
                  'Use the prepared cases and demo plan. Confirm the actual recording opens and the isolated reviewer access works. Enter credentials only in the portal’s secure fields.',
                  'Does the recording open, and is the reviewer access ready?',
                  recording_url=snapshot.get('demo_recording_url'), source_url=SUBMISSION)))
    if features['desktop']:
        cards.append((_confirmed(a.get('desktop-install', {})),
            _card('desktop-install', 'Check a clean desktop installation', 'human',
                  'Install the exact prepared ZIP in a clean supported desktop environment and exercise its main workflows. Retain a trace or observation reference.',
                  'Did the clean desktop installation and main workflows succeed?', source_url=DESKTOP)))
    cards.append((_confirmed(a.get('creator-facts', {}), ('publisher', 'rights', 'data_practices', 'support')),
        _card('creator-facts', 'Confirm the creator-owned facts', 'human',
              'Show the drafted publisher, rights, data-practice and support statements. Reuse verified facts and ask the creator to correct or confirm the remaining claims; never preselect legal declarations.',
              'Are the prepared publisher, rights, data practices and support statements accurate for this target?',
              statements=dict(publisher=state['snapshot']['facts']['publisher'],
                rights='I am authorized to distribute the supplied source and assets.',
                data_practices='The prepared description of actual data access and handling is accurate.',
                support='The supplied support destination is mine to provide and will help users.'),source_url=SUBMISSION)))
    return cards


def _portal(state):
    a = state['answers']; features = state['snapshot']['features']
    checks = ['metadata_passed', 'skills_passed'] if features['skills'] else ['metadata_passed']
    if features['remote_mcp']:
        checks += ['mcp_passed', 'review_materials_checked']
    return [
        (_confirmed(a.get('upload', {})), _card('upload', 'Upload the prepared ZIP', 'human',
            'Open the official submission portal from the linked guide, select the owning organization/project and verified identity, and upload the exact attached ZIP. Use the existing plugin when updating. For approved local MCP choose the desktop route described in its guide.',
            'Which plugin and draft/release did the portal create or update?', artifacts=state['artifacts'], source_url=SUBMISSION)),
        (_confirmed(a.get('portal-validation', {}), tuple(checks)), _card('portal-validation', 'Resolve the portal findings', 'human',
            'Check the imported identity, version, metadata and skills. For remote MCP, verify the connected server, authentication, scans and review details. Bring copied issues back here: I will map them to source changes and prepare a corrected package.',
            'Have the applicable portal checks succeeded, or what issues did it report?', required_checks=checks,
            last_report=a.get('portal-validation', {}), source_url=SUBMISSION)),
        (_confirmed(a.get('submit-review', {})), _card('submit-review', 'Submit the verified draft for review', 'human',
            'Use the prepared copy fields and applicable review materials. Confirm the selected plugin and draft, complete creator-owned declarations yourself, and submit in the portal.',
            'Has this exact draft been submitted for review?', source_url=SUBMISSION)),
        (a.get('review-decision', {}).get('decision') == 'approved', _card('review-decision', 'Track the review decision', 'human',
            'Check the portal when a decision is available. Return pending, approved, rejected or changes-requested with the actual reference. I will help resolve feedback; elapsed time is never approval.',
            'What review status does the portal show?', last_report=a.get('review-decision', {}), source_url=SUBMISSION)),
        (_confirmed(a.get('publish', {})), _card('publish', 'Publish when you choose', 'human',
            'The current draft has creator-reported approval. Check the final listing and publish it in the portal when ready. Return the public listing reference.',
            'Have you published this approved release?', source_url=SUBMISSION)),
    ]


def next_step(state):
    """One current action; prerequisite gates cannot be bypassed by later answers."""
    if state['paused']:
        card = _card('resume', 'Submission wizard paused', 'human', 'Resume this saved session when ready.', 'Would you like to resume?')
    elif state.get('source_pending'):
        card=_card('plugin-root','Select the plugin in this repository','human','I found multiple plausible plugin roots. Choose the integration to prepare.','Which plugin should I prepare?',roots=state['source_pending']['roots'])
    elif not state.get('snapshot'):
        card = _card('source', 'Load your target', 'human', 'Attach the plugin ZIP or select its source folder. Existing audit outputs can be imported with their exact target.', 'Which plugin should we prepare?')
    elif not state['answers'].get('goal'):
        card = _card('goal', 'Choose the outcome', 'human', 'I have inspected the target. Choose the scope so the wizard applies the right gates.', 'Do you want an audit or guided public submission?', choices=['Audit', 'Guided public submission'])
    elif state['answers']['goal']['goal'] == 'audit':
        card = _card('done', 'Audit complete', 'assistant', 'Explain the findings, link the inspected artifacts and offer the next repair or guided submission step.', findings=state['snapshot']['package_report']['issues'])
    elif state['answers']['goal']['goal'] == 'private-preparation':
        pending=[c for passed,c in _preparation(state) if not passed]
        card=pending[0] if pending else _card('done','Private preparation complete','assistant',
            'Present the prepared package, inferred tasks and available checks. No public submission or publication action was requested.')
    else:
        prep = _preparation(state)
        pending = [c for passed, c in prep if not passed]
        active = [c for c in pending if c['id'] not in state['deferred']]
        if active or pending:
            card = (active or pending)[0]
            if card['id'] in state['deferred']:
                card['deferred_reason'] = state['deferred'][card['id']]
        else:
            card = next((c for passed, c in _portal(state) if not passed), None)
            if card is None:
                card = _card('done', 'Simulation complete' if state['synthetic'] else 'Publication reported by the creator', 'assistant',
                    'Present the source binding, evidence, prepared artifacts and recorded external status. Observer identity and portal execution are not independently authenticated.')
            elif card['id'] == 'portal-validation' and state['answers'].get('portal-validation', {}).get('issues'):
                card.update(title='Repair the portal findings', actor='assistant', question=None,
                    instruction='Inspect the copied portal issues, identify the affected source or server setup, make authorized repairs and rerun the relevant checks. Guide a corrected upload only when the package changed; otherwise revisit portal-validation after the applicable reconnect/rescan or human correction.')
            elif card['id'] == 'review-decision' and state['answers'].get('review-decision', {}).get('decision') in ('changes-requested', 'rejected'):
                card['title'] = 'Resolve the review feedback'
                card['actor'] = 'assistant' if state['answers']['review-decision'].get('feedback') else 'human'
                card['question'] = None if card['actor'] == 'assistant' else 'What feedback did the review team provide?'
                card['instruction'] = 'Inspect the supplied feedback, repair the requested source or review materials, and revisit the affected gates. Prepare a new ZIP if source changed; keep the earlier decision in history.'
    progress = []
    if state.get('snapshot') and state['answers'].get('goal', {}).get('goal') == 'public-submission':
            progress = [dict(id=c['id'], status=c.get('completion_status','Completed') if passed else 'Deferred' if c['id'] in state['deferred'] else 'Pending')
                    for passed, c in _preparation(state) + _portal(state)]
    portal_ready = bool(state.get('snapshot')) and state['answers'].get('goal', {}).get('goal') == 'public-submission' and all(p for p, _ in _preparation(state))
    return dict(session_id=state['session_id'], revision=state['revision'], next=card, progress=progress,
                notice=state.get('notice'), simulation=state['synthetic'],
                ready_for_human_portal=portal_ready and not state['synthetic'],
                simulated_preparation_complete=portal_ready and state['synthetic'],
                actual_host_execution_authenticated=False, portal_actions_performed_by_tool=False,
                submitted=not state['synthetic'] and _confirmed(state['answers'].get('submit-review', {})),
                published=not state['synthetic'] and _confirmed(state['answers'].get('publish', {})),
                external_status_provenance='Creator-reported; not independently authenticated', artifacts=state['artifacts'])


def question_plan(state):
    """Native provider schema plus a separate stable label/ID map; no invented UI fields."""
    card=next_step(state)['next'];step=card['id'];choices=state.get('choices',{});mode=choices.get('editing','setup')
    options=[];kind='single_select';question=card.get('question') or card['title']
    if step in ('package','requirement-review') and state.get('proposed_fix'):
        options=[('apply','Apply the suggested fix'),('details','Inspect the prepared changes'),('adjust','Adjust the supported claim')]
        question=state['proposed_fix']['summary']
    elif step=='plugin-root':
        page=state['source_pending'].get('page',0);roots=card['roots'];start=page*8
        options=[(root,root or 'Repository root') for root in roots[start:start+8]]
        if start+8<len(roots):options.append(('/next','Show more plugins'))
        if page:options.append(('/previous','Show previous plugins'))
        if len(options)==1:options.append(('/refresh','Recheck the repository'))
    elif step=='understanding':
        if mode in ('tasks','boundaries'):
            items=state['understanding'][mode];page=choices.get('page',0)
            options=[(item['id'],item['label'][:160]) for item in items[page*10:(page+1)*10]]
            kind='multi_select';question='Select the '+mode+' to include (page '+str(page+1)+').'
            if len(options)==1: options.append(('none','Leave this item out'))
        elif mode=='audience':options=[('public','Public directory submission'),('private','Prepare for private use'),('hosts','Change intended hosts')]
        elif mode=='hosts':options=[('chatgpt','ChatGPT'),('codex','Codex'),('both','ChatGPT and Codex')]
        else:options=[('accept','Use suggested setup'),('tasks','Adjust supported tasks'),('boundaries','Adjust boundary examples'),('audience','Change audience or host')]
    elif step=='hosts':options=[('chatgpt','ChatGPT'),('codex','Codex'),('both','Both')]
    elif step=='goal':options=[('public-submission','Prepare public submission'),('audit','Audit this target')]
    elif step in ('creator-facts','review-materials','desktop-install'):
        options=[('confirm','Confirm the prepared statements'),('adjust','Review or adjust the prepared statements'),('later','Continue other preparation')]
    elif step in ('upload','portal-validation','submit-review','publish'):
        options=[('confirm','The described portal step succeeded'),('issues','The portal reported an issue'),('later','Save and continue later')]
    elif step=='review-decision':options=[('pending','Pending'),('approved','Approved'),('changes-requested','Changes requested'),('rejected','Rejected')]
    if not options:return None
    labels=[label for _,label in options]
    # Duplicate descriptions must never make a native selection ambiguous.
    if len(set(labels))!=len(labels):options=[(ident,label+' ('+ident+')') for ident,label in options]
    ident=digest(dict(step=step,mode=mode,options=options,source=binding(state),draft=meaning(state.get('understanding')),revision=state['revision']))[:24]
    payload={'ask_user_input':{'questions':[dict(question=question,options=[label for _,label in options],type=kind,
        free_text_placeholder='Add a specific correction (optional)')]}}
    return dict(id=ident,revision=state['revision'],step=step,mode=mode,options=[dict(id=i,label=l) for i,l in options],
        binding=binding(state),suggested_defaults=dict(audience=choices.get('audience','public'),hosts=state['answers'].get('hosts',{}).get('hosts',['chatgpt']),
            repository_visibility=state.get('source_origin',{}).get('visibility','unknown'),
            data_access=(state.get('understanding') or {}).get('data_access'),publication_intent='Prepare the selected route; final portal action remains a creator choice'),
        payload=payload,rendering='Emit the ask_user_input payload as the native GenUI widget, then end the turn.')


def apply_choices(state, response, now):
    plan=state.get('question_plan')
    if not plan or response.get('question_id')!=plan['id'] or response.get('revision')!=plan['revision'] or state['revision']!=plan['revision']:
        raise ValueError('This question changed; render the current native choice')
    if binding(state)!=plan['binding']:raise ValueError('Choice belongs to a different target or test plan')
    selected=response.get('selected',[])
    if not isinstance(selected,list):raise ValueError('Return selected option IDs or labels as a list')
    mapping={o['id']:o['id'] for o in plan['options']};mapping.update({o['label']:o['id'] for o in plan['options']})
    if len(selected)!=len(set(selected)) or any(v not in mapping for v in selected):raise ValueError('Select unique options from the current question')
    ids=[mapping[v] for v in selected];kind=plan['payload']['ask_user_input']['questions'][0]['type']
    if kind=='single_select' and len(ids)!=1:raise ValueError('Choose exactly one option')
    state=copy.deepcopy(state);step=plan['step'];value=ids[0] if ids else None
    if response.get('correction'):
        state['pending_correction']=response['correction'];state['choices']['confirmed']=False;state['question_plan']=None
        return event(state,'creator-correction',{'step':step,'correction':response['correction']},now)
    if step in ('package','requirement-review') and state.get('proposed_fix'):
        if value=='apply':state['apply_proposal']=True
        elif value=='adjust':state['pending_correction']='Revise the supported claim to address the current finding.'
        else:state['notice']='Show the prepared replacement diff, then reuse this choice.'
    elif step=='plugin-root':
        if value=='/next':state['source_pending']['page']=state['source_pending'].get('page',0)+1
        elif value=='/previous':state['source_pending']['page']=max(0,state['source_pending'].get('page',0)-1)
        elif value=='/refresh':state['source_pending']['page']=0
        else:state['selected_root']=value
    elif step=='understanding':
        c=state['choices'];mode=plan['mode']
        if mode=='setup':
            if value=='accept':
                state.pop('legacy_binding',None)
                c.update(confirmed=True,task_ids=c.get('task_ids',[t['id'] for t in state['understanding']['tasks']]),
                    boundary_ids=c.get('boundary_ids',[b['id'] for b in state['understanding']['boundaries']]),
                    audience=c.get('audience','public'),confirmation_question=plan['id'])
                if not c['task_ids']:raise ValueError('Select at least one intended task or choose private/audit preparation')
                state['answers']['test-plan']={'cases':derive_test_plan(state)}
            else:c.update(editing=value,page=0,pending=[])
        elif mode in ('tasks','boundaries'):
            c['pending']=c.get('pending',[])+[i for i in ids if i!='none'];c['page']=c.get('page',0)+1
            if c['page']*10>=len(state['understanding'][mode]):
                c['task_ids' if mode=='tasks' else 'boundary_ids']=c.pop('pending');c.update(editing='setup',page=0)
        elif mode=='audience':
            if value=='hosts':c['editing']='hosts'
            else:
                c.update(audience=value,editing='setup')
                state['answers']['goal']={'goal':'public-submission' if value=='public' else 'private-preparation'}
        elif mode=='hosts':
            state.pop('legacy_binding',None)
            state['answers']['hosts']={'hosts':['chatgpt','codex'] if value=='both' else [value]};c['editing']='setup'
    elif step in ('goal','hosts'):
        state.pop('legacy_binding',None)
        state['answers'][step]={'goal':value} if step=='goal' else {'hosts':['chatgpt','codex'] if value=='both' else [value]}
    elif value=='later':
        if step in DEFERABLE:state['deferred'][step]='Deferred by creator selection'
        else:state['paused']=True
    else:
        # Actual portal IDs, observed URLs and corrections come from the host's
        # observation adapter, never from a yes/no label alone.
        observation=response.get('observation',{})
        if value=='confirm' and step in ('creator-facts','review-materials','desktop-install'):
            fields={'creator-facts':['publisher','rights','data_practices','support'],
                    'review-materials':['recording_accessible','reviewer_access_ready'],'desktop-install':['confirmed']}[step]
            observation.update({k:True for k in fields})
            observation.update(confirmed_by='Creator through native Q&A',reference='question:'+plan['id'])
        elif step=='review-decision':observation['decision']=value
        elif value=='confirm':observation['confirmed']=True
        else:
            state['notice']='Inspect the reported issue or revise the prepared statements; prior confirmation was not assumed.'
            state['question_plan']=None
            return event(state,'choice-needs-observation',{'step':step,'selected':ids},now)
        validate_answer(state,step,observation);state['answers'][step]=observation
    state['question_plan']=None
    return event(state,'native-choice',dict(question_id=plan['id'],step=step,mode=plan['mode'],selected_ids=ids,
        correction=response.get('correction'),provider='chatgpt.app',draft_sha256=meaning(state.get('understanding'))),now)


def derive_test_plan(state):
    draft=state['understanding'];c=state['choices'];cases=[]
    for task in draft['tasks']:
        if task['id'] not in c.get('task_ids',[]):continue
        for kind,key in [('direct','direct_prompt'),('indirect','indirect_prompt')]:
            cases.append(dict(id=task['id']+':'+kind,prompt=task[key],expected=task['expected'],task_id=task['id'],kind=kind))
    for boundary in draft['boundaries']:
        if boundary['id'] in c.get('boundary_ids',[]):cases.append(dict(id='boundary:'+boundary['id'],prompt=boundary['prompt'],expected=boundary['expected'],kind='negative'))
    for n,case in enumerate(state['snapshot'].get('review_cases',[])):
        prompt=case.get('prompt',case.get('userPrompt'))
        if prompt and not any(c['prompt']==prompt and c.get('server')==case.get('server') for c in cases):
            row=dict(id='review:'+str(n),prompt=prompt,expected=case.get('expected_behavior',case.get('expectedOutput','Do not perform an unsupported action; explain the appropriate next step.')),kind=case.get('kind','review'))
            if case.get('server'):row['server']=case['server']
            cases.append(row)
    return cases


def validate_answer(state, step, value):
    if not isinstance(value, dict):
        raise ValueError('A step response must be an object')
    def check_keys(item):
        if isinstance(item, dict):
            if any(str(k).lower() in ('password', 'token', 'credentials', 'api_key', 'access_token', 'refresh_token', 'client_secret', 'mfa_code') for k in item):
                raise ValueError('Keep credentials in the portal secure fields, outside wizard responses')
            for v in item.values(): check_keys(v)
        elif isinstance(item, list):
            for v in item: check_keys(v)
    check_keys(value)
    if step == 'goal':
        if value.get('goal') not in ('audit', 'public-submission','private-preparation'):
            raise ValueError('Choose audit, private-preparation or public-submission')
    elif step == 'hosts':
        hosts = value.get('hosts')
        if not isinstance(hosts, list) or not hosts or len(hosts) != len(set(hosts)) or any(h not in ('chatgpt', 'codex') for h in hosts):
            raise ValueError('Choose unique intended hosts: chatgpt and/or codex')
    elif step == 'test-plan':
        cases = value.get('cases')
        if not isinstance(cases, list) or not cases or len(cases) > 500:
            raise ValueError('Supply 1 to 500 source-derived cases')
        ids = []
        for case in cases:
            if not isinstance(case, dict) or not all(nonempty(case.get(k)) for k in ('id', 'prompt', 'expected')):
                raise ValueError('Each case needs id, prompt and independently derived expected behavior')
            ids.append(case['id'])
        if len(ids) != len(set(ids)):
            raise ValueError('Case IDs must be unique')
        review_cases = (state.get('snapshot') or {}).get('review_cases', [])
        if (state.get('snapshot') or {}).get('features', {}).get('remote_mcp'):
            missing = [r for r in review_cases if not any(c['prompt'] == r.get('prompt', r.get('userPrompt')) for c in cases)]
            if missing:
                raise ValueError('Include every supplied remote review prompt in the host plan')
    elif step == 'requirement-review':
        decisions = value.get('decisions')
        known = {r['id'] for r in state['snapshot']['facts']['requirement_catalog']} | {r['id'] for r in state.get('findings',[])}
        if not isinstance(decisions, list) or not decisions:
            raise ValueError('Record the remaining requirement dispositions')
        seen = set()
        for row in decisions:
            if not isinstance(row, dict) or row.get('id') not in known or row['id'] in seen:
                raise ValueError('Requirement IDs must be known and unique')
            seen.add(row['id'])
            if row.get('status') not in ('Passed', 'Not applicable', 'Failed', 'Blocked', 'Not run') or not all(nonempty(row.get(k)) for k in ('observed_result', 'evidence_reference')):
                raise ValueError('Each disposition needs status, actual observation and evidence reference')
            if 'evidence' in row:
                evidence = row['evidence']
                if not isinstance(evidence, dict) or not nonempty(evidence.get('sha256')) or len(evidence['sha256']) != 64 or any(c not in '0123456789abcdef' for c in evidence['sha256']):
                    raise ValueError('Requirement evidence needs an exact SHA-256')
                if bool(evidence.get('file')) == bool(evidence.get('source_path')):
                    raise ValueError('Choose one local evidence file or frozen-source path')
    elif step == 'allowlist':
        if value.get('status') != 'allowlisted' or not all(nonempty(value.get(k)) for k in ('organization_id', 'confirmed_by', 'confirmed_at', 'evidence_reference')):
            raise ValueError('Supply the actual organization allowlist confirmation and its reference')
        if datetime.fromisoformat(value['confirmed_at'].replace('Z', '+00:00')).tzinfo is None:
            raise ValueError('Allowlist confirmation needs a timezone')
        if value.get('synthetic') is True and not state['synthetic']:
            raise ValueError('A synthetic confirmation cannot establish actual eligibility')
    elif step in HUMAN:
        if not all(nonempty(value.get(k)) for k in ('confirmed_by', 'reference')):
            raise ValueError('Identify the actual observer and evidence reference; never supply credentials')
        if step in ('upload', 'portal-validation', 'submit-review', 'review-decision', 'publish'):
            if not all(nonempty(value.get(k)) for k in ('plugin_reference', 'release_reference')):
                raise ValueError('Record the actual plugin and draft/release reference')
            uploaded = state['answers'].get('upload', {})
            if step != 'upload' and any(value[k] != uploaded.get(k) for k in ('plugin_reference', 'release_reference')):
                raise ValueError('Portal response refers to a different plugin or release')
        if step == 'upload' and value.get('package_sha256') != state['snapshot']['package_sha256']:
            raise ValueError('Upload confirmation must identify the exact prepared archive SHA-256')
        if step == 'review-decision' and value.get('decision') not in ('pending', 'approved', 'changes-requested', 'rejected'):
            raise ValueError('Record pending, approved, changes-requested or rejected')
        if step == 'publish' and value.get('confirmed') is True:
            url = urlsplit(value.get('listing_url', ''))
            if url.scheme != 'https' or not url.hostname or url.username or url.password:
                raise ValueError('Provide the actual HTTPS public listing URL without credentials')
    else:
        raise ValueError('This step is completed through source inspection or report ingestion')
    return value


def answer(state, step, value, now):
    current = next_step(state)['next']['id']
    if current != step:
        raise ValueError('Expected step '+current+'; later gates cannot be skipped')
    validate_answer(state, step, value)
    state = copy.deepcopy(state)
    if step == 'requirement-review':
        previous = {r['id']: r for r in state['answers'].get(step, {}).get('decisions', [])}
        previous.update({r['id']: copy.deepcopy(r) for r in value['decisions']})
        state['answers'][step] = {'decisions': list(previous.values())}
        for row in value['decisions']:
            if row.get('evidence_state') in ('Imported artifact integrity checked','Frozen source digest checked'):
                for finding in state.get('findings',[]):
                    if finding['id']==row['id']:finding.update(status=row['status'],resolution=row)
    else:
        state['answers'][step] = copy.deepcopy(value)
        if step in ('goal','hosts','test-plan'):state.pop('legacy_binding',None)
    if step=='test-plan':state.pop('plan_editing',None)
    state['deferred'].pop(step, None)
    return event(state, 'step-response', {'step': step, 'value': value}, now)


def revisit(state, step, now):
    if step not in ORDER or step in ('source', 'package'):
        raise ValueError('Choose an editable intake, plan, confirmation or portal step')
    state = copy.deepcopy(state)
    if step=='understanding':
        state['choices'].update(confirmed=False,editing='setup');state['question_plan']=None
    if step=='test-plan':state['plan_editing']=True
    remove = ORDER[ORDER.index(step):]
    previous = {k: v for k, v in state['answers'].items() if k in remove}
    for key in remove:
        if key == 'hosts' and step != 'hosts':
            continue  # Host selection is creator intent, not package execution evidence.
        state['answers'].pop(key, None); state['deferred'].pop(key, None)
    if ORDER.index(step) <= ORDER.index('host-tests'):
        state['host_rows'] = {}
    if ORDER.index(step) <= ORDER.index('test-plan'):
        state['artifacts'] = {}
    return event(state, 'revisit', {'step': step, 'invalidated_answers': previous}, now)


def defer(state, reason, now):
    step = next_step(state)['next']['id']
    if step not in DEFERABLE or not nonempty(reason):
        raise ValueError('Only preparation evidence tasks can be deferred, with a reason')
    state = copy.deepcopy(state); state['deferred'][step] = reason
    return event(state, 'deferred', {'step': step, 'reason': reason}, now)
