"""Inspect a loaded target and create concrete preflight records without executing it."""
import hashlib
import json
import re
from pathlib import Path


def plugin_roots(files):
    """Root manifest wins over bundled fixtures; otherwise expose real alternatives."""
    if 'plugin.json' in files or '.codex-plugin/plugin.json' in files: return ['']
    roots = set()
    for name in files:
        if name.endswith('/plugin.json') and not any(p in name.split('/') for p in ('tests','fixtures','node_modules','examples','assets')):
            root = name[:-len('/plugin.json')]
            if root.endswith('/.codex-plugin'): root = root[:-len('/.codex-plugin')]
            roots.add(root)
    return sorted(roots) or ['']


def source_details(files, checker):
    """Inventory declarations and implementation entrypoints without executing them."""
    tools = []; skills = []; seen = set()
    for name, data in sorted(files.items()):
        if any(p in name.split('/') for p in ('tests','fixtures','evals','node_modules','references','assets')): continue
        text = data.decode('utf-8', errors='replace')
        if name.startswith('skills/') and name.endswith('/SKILL.md'):
            match = re.search(r'^description:\s*(.+)$', text, re.M)
            skills.append(dict(id='skill:'+name.split('/')[1], name=name.split('/')[1],
                description=match[1].strip(' "\'') if match else name.split('/')[1], path=name))
        for match in re.finditer(r'(?:registerTool|\.tool)\s*\(\s*[\'\"]([^\'\"]+)[\'\"]', text):
            snippet = text[match.start():match.start()+1800]
            description = re.search(r'description\s*:\s*[\'\"`]([^\'\"`]+)', snippet)
            tool = dict(name=match[1], description=description[1] if description else match[1].replace('_',' '),
                        source_path=name, source_excerpt=snippet[:700], origin='Source registration; runtime inventory not executed')
            if tool['name'] not in seen: tools.append(tool); seen.add(tool['name'])
        for match in re.finditer(r'@\w+(?:\.\w+)*\.tool\([^)]*\)\s*(?:async\s+)?def\s+(\w+)\(', text):
            snippet = text[match.start():match.start()+1400]
            doc = re.search(r'"""(.*?)"""|\'\'\'(.*?)\'\'\'', snippet, re.S)
            tool = dict(name=match[1], description=(' '.join((doc[1] or doc[2]).split()) if doc else match[1].replace('_',' ')),
                        source_path=name, source_excerpt=snippet[:700], origin='Source registration; runtime inventory not executed')
            if tool['name'] not in seen: tools.append(tool); seen.add(tool['name'])
        if name in ('tools.json','tools-list.json','mcp-tools.json'):
            try:
                value = json.loads(text)
                for supplied in value.get('tools',[]) if isinstance(value,dict) else []:
                    if isinstance(supplied,dict) and isinstance(supplied.get('name'),str) and supplied['name'] not in seen:
                        tools.append(dict(supplied,source_path=name,origin='Supplied inventory definition; live discovery not executed'))
                        seen.add(supplied['name'])
            except ValueError: pass
    features = {}
    evidence = {}
    def detect(key, predicate):
        matches = [t for t in tools if predicate(t, json.dumps(t).lower())]
        features[key] = bool(matches); evidence[key] = [dict(path=t['source_path'], tool=t['name']) for t in matches]
    detect('local_services_quote', lambda t,s: bool(re.search(r'(?:request|create).*quote',t['name'],re.I)) and bool(re.search(r'local.service|service_type|servicetype',s)) and bool(re.search(r'address|location|postal',s)))
    detect('product_checkout', lambda t,s: bool(re.search(r'(?:create|start).*checkout|checkout_session',t['name'],re.I)) and bool(re.search(r'line_items|products|cart',s)))
    detect('restaurant_reservation', lambda t,s: bool(re.search(r'reserve_table|restaurant.*reservation|book_restaurant',t['name'],re.I)) and bool(re.search(r'party_size|partysize|restaurant_id',s)))
    all_code = '\n'.join(data.decode('utf-8', errors='replace') for n,data in files.items()
        if n.endswith(('.py','.ts','.js','.json')) and not any(p in n.split('/') for p in ('tests','fixtures','evals','references','assets')))
    def obj(value):return value if isinstance(value,dict) else {}
    features.update(ui=any(isinstance(t.get('_meta'),dict) and ('ui/resourceUri' in t['_meta'] or isinstance(t['_meta'].get('ui'),dict) and t['_meta']['ui'].get('resourceUri')) for t in tools) or bool(re.search(r'[\'\"](?:mimeType|resourceUri|uri)[\'\"]\s*:\s*[\'\"](?:text/html|ui://)',all_code)),
                    events=bool(re.search(r'[\'\"]method[\'\"]\s*:\s*[\'\"](?:notifications/events|subscriptions/create)',all_code)),
                    extensions=bool(checker.settings.get('extensions')),
                    auth=any(obj(obj(obj(s.get('extensions')).get('com.openai')).get('auth')).get('type') in ('oauth','mixed','api_key') for s in checker.servers.values() if isinstance(s,dict)),
                    responses_api=bool(re.search(r'\.responses\.create\s*\(|(?:post|fetch|request)\s*\([^\n]{0,160}/v1/responses',all_code)),
                    evaluations=any(n.startswith(('tests/','evals/')) for n in files))
    return dict(tools=tools, skills=skills, detected=features, capability_evidence=evidence,
                readme=next((data.decode('utf-8',errors='replace')[:16000] for n,data in files.items() if n.lower()=='readme.md'),''))


def draft_understanding(facts, details):
    """Useful source-backed defaults; the host can refine them through the same contract."""
    tasks = []
    for entry in details['skills'] + details['tools']:
        is_skill = 'id' in entry
        ident = entry.get('id', 'tool:'+entry['name'])
        description = entry.get('description')
        description = description.strip() if isinstance(description,str) and description.strip() else entry['name'].replace('_',' ')
        label = description.split('.')[0][:100] or entry['name']
        tasks.append(dict(id=ident, label=label, description=description,
            source_paths=[entry.get('path',entry.get('source_path'))],
            provenance='Source declaration; inferred product meaning',
            direct_prompt=('Use '+facts['name']+' to '+label[0].lower()+label[1:]+'.'),
            indirect_prompt=label.rstrip('.')+'.',
            expected='Complete the declared workflow: '+description,
            supported=True))
    if not tasks:
        tasks.append(dict(id='declared-workflow',label='Use the declared integration',
            description=facts['listing'].get('longDescription', facts['name']),
            source_paths=[facts['audit_observation']['manifest_path']], provenance='Listing declaration; implementation needs agent inspection',
            direct_prompt='Use '+facts['name']+' for its described workflow.',
            indirect_prompt='Help me complete the described workflow.',
            expected='Complete only capabilities supported by inspected implementation.',supported=False))
    boundaries = [dict(id='unrelated',label='Route unrelated tasks to the appropriate tool',
                      prompt='Translate a short sentence unrelated to this integration.',expected='Use the appropriate general capability; do not invoke unrelated integration operations.'),
                  dict(id='missing-context',label='Ask for missing input before taking an action',
                      prompt='Do the main task without the required input.',expected='Ask only for the missing input; do not invent it or claim completion.'),
                  dict(id='undeclared-action',label='Explain an operation the integration does not support',
                      prompt='Perform an operation outside the listed integration tasks.',expected='Explain the actual supported alternative without claiming an unavailable action.')]
    return dict(schema_version=1, summary=facts['listing'].get('longDescription') or facts['listing'].get('shortDescription') or facts['name'],
        personas=[dict(id='primary-user',label='People who need '+(tasks[0]['label'].lower()),provenance='Inferred from declared workflow')],
        tasks=tasks,boundaries=boundaries,claims=[dict(task_id=t['id'],text=t['label']) for t in tasks if t['supported']],
        data_access=dict(description=facts['permissions'],provenance='Declared connection/host capabilities; source refinement may add observed details'),
        ambiguities=[dict(code='implementation-unknown',task_id=t['id'],message='Inspect implementation before advertising this capability.') for t in tasks if not t['supported']],
        provenance='Automatic source draft; creator choices confirm intent, not execution')


def inspect_target(source, catalog, submission_route='remote', allowlist=None, synthetic=False, profile='package', rule_context=None):
    import check_package
    files = check_package.load_files(Path(source))
    checker = check_package.Checker(files, 'openai', profile, submission_route=submission_route,
                                    desktop_allowlist=allowlist, synthetic=synthetic, rule_context=rule_context)
    report = checker.run()
    manifest = checker.manifest
    settings = checker.settings
    interface = settings.get('interface', {}) if isinstance(settings, dict) else {}
    if not isinstance(interface,dict):interface={}
    skill_paths = sorted(n for n in files if n.startswith('skills/') and n.count('/') == 2 and n.endswith('/SKILL.md'))
    server_specs = checker.servers
    remote = any(isinstance(s, dict) and 'url' in s for s in server_specs.values())
    local = any(isinstance(s, dict) and 'command' in s for s in server_specs.values())
    features = dict(skills=bool(skill_paths), mcp=bool(server_specs) or checker.unresolved,
                    remote_mcp=remote, desktop=local or settings.get('requires_local_executor') is True,
                    ui=False, events=False, extensions=False, commerce=False, migration=False, api=False,
                    quote=False, checkout=False, reservation=False)
    def obj(value):return value if isinstance(value,dict) else {}
    auth_declarations = [obj(obj(obj(s.get('extensions')).get('com.openai')).get('auth')).get('type')
                         for s in server_specs.values() if isinstance(s, dict)]
    anonymous = bool(auth_declarations) and all(mode == 'none' for mode in auth_declarations)
    # Optional server features cannot be inferred from a package description.
    declared = {'ui': 'Not discoverable without actual tool/resource inventory' if features['mcp'] else 'No MCP declaration',
                'events': 'Requires server discovery' if features['mcp'] else 'No MCP declaration'}
    archive_hash = hashlib.sha256(Path(source).read_bytes()).hexdigest() if Path(source).is_file() else None
    inventory = [{'path': n, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)} for n, data in sorted(files.items())]
    review = checker.review_settings.get('review', {})
    review = review if isinstance(review, dict) else {}
    try:
        eval_cases=json.loads(files.get('evals/cases.json', b'[]'))
        eval_count=len(eval_cases) if isinstance(eval_cases,list) else 0
    except (ValueError,UnicodeError):eval_count=0
    observation = dict(name=manifest.get('name'), version=manifest.get('version'), manifest_path=checker.manifest_path,
                       package_format=report['format'], component_kind=report['classification']['kind'],
                       skill_paths=skill_paths, server_names=sorted(server_specs), components=features,
                       feature_discovery=declared, file_count=len(files), content_sha256=report['content_sha256'],
                       package_sha256=archive_hash, display_name=interface.get('displayName'),
                       starter_prompts=([p for p in interface.get('defaultPrompt',[]) if isinstance(p,str)] if isinstance(interface.get('defaultPrompt',[]),list) else [interface['defaultPrompt']] if isinstance(interface.get('defaultPrompt'),str) else []),publisher=obj(manifest.get('author')),
                       declared_host_capabilities=[v for v in interface.get('capabilities',[]) if isinstance(v,str)] if isinstance(interface.get('capabilities',[]),list) else [],
                       native_eval_cases=sum(n.startswith('evals/') and n.endswith('/prompt.md') for n in files),
                       json_eval_cases=eval_count,
                       integration_endpoints_contacted=False, source_executed=False,
                       portal_actions_performed=False, monitoring_active=False, synthetic=synthetic,
                       check_profile=profile, submission_route=submission_route,
                       demo_recording_url=review.get('demo_recording_url'))
    result_by_id = {}
    for req in catalog:
        scope = req['scope']
        status = 'Not run'
        reason = 'Requires target-specific human review or product-host observation; not established by static inspection.'
        if scope == 'human':
            status = 'Not applicable'
            reason = 'Portal identity, upload, review and publication are explicit external human handoffs for this preflight audit.'
        elif scope != 'any' and not features.get(scope):
            status = 'Not applicable' if not features['mcp'] or scope in ('skills','desktop','remote_mcp','migration','api','quote','checkout','reservation') else 'Not run'
            reason = ('The loaded target declares no applicable '+scope+' integration. This is not an unsupported meta-tool claim.'
                      if status == 'Not applicable' else 'The package does not establish this optional server feature; discover actual capabilities before applying its rules.')
        elif req['id'].startswith('SS-AUTH-') and anonymous:
            status = 'Not applicable'; reason = 'The server declarations explicitly select anonymous access. Protected-operation OAuth requirements do not apply; actual permission boundaries remain unverified.'
        elif req['id'] in ('SS-ARCH-01', 'SS-ARCH-03'):
            status = 'Passed'; reason = 'The effective manifest and packaged skill inventory establish the selected component structure.'
        elif req['id'] == 'SS-SKILL-01':
            errors = [i for i in report['issues'] if i['severity'] == 'error' and ('skill' in i['code'])]
            status = 'Failed' if errors else 'Passed'
            reason = 'Static skill entrypoint/frontmatter and contained reference checks completed; behavior remains a separate check.'
        elif req['id'] in ('SS-PKG-01', 'SS-REVIEW-02'):
            status = 'Passed' if report['status'] == 'local_checks_passed' else 'Failed'
            reason = 'Executed the '+profile+' profile against the loaded target; final directory and human attestation gates are explicitly separate.'
        elif req['id'] == 'SS-PKG-02':
            portable = json.loads(files.get('plugin.json', b'{}'))
            overlay = json.loads(files.get('.codex-plugin/plugin.json', b'{}'))
            matched = not overlay or all(portable.get(k) == overlay.get(k) for k in ('name','version'))
            status = 'Passed' if matched else 'Failed'; reason = 'Compared identity/version in the portable and compatibility manifests.'
        elif req['id'] == 'SS-EVAL-01':
            reason = (f"Observed {observation['json_eval_cases']} JSON scenario definitions and {observation['native_eval_cases']} native prompt folders. "
                      'Definitions are source evidence, not executed agent results; actual grading remains unverified.')
        elif scope == 'skills' and not features['skills']:
            status = 'Not applicable'; reason = 'No skill entrypoint is declared in the loaded target.'
        result_by_id[req['id']] = dict(status=status, observed_result=reason,
                                       evidence=['evidence/requirements/'+req['id']+'.json'])
    connection = {}
    auth_mode = 'none' if not features['mcp'] else 'unknown'
    if len(server_specs) == 1:
        spec = next(iter(server_specs.values()))
        if isinstance(spec, dict):
            if 'url' in spec:
                connection = {'transport': 'http', 'url': spec['url']}
            elif 'command' in spec:
                connection = {'transport': 'stdio', 'command': spec['command'], 'args': spec.get('args', [])}
                if 'cwd' in spec:
                    connection['cwd'] = spec['cwd']
            auth = obj(obj(spec.get('extensions')).get('com.openai')).get('auth', {})
            auth_mode = auth.get('type', auth_mode) if isinstance(auth, dict) else auth_mode
    defined_cases = review.get('test_cases', {}) if isinstance(review, dict) else {}
    review_cases = []
    if isinstance(defined_cases, dict):
        for kind in ('positive', 'negative'):
            for case in defined_cases.get(kind, []) if isinstance(defined_cases.get(kind, []), list) else []:
                if isinstance(case, dict):
                    review_cases.append({'kind': kind, 'origin': 'Observed package definition; execution not established', **case})
    for server,spec in server_specs.items():
        per_server=obj(obj(obj(obj(spec).get('extensions')).get('com.openai')).get('review'))
        for kind,key in (('positive','testCases'),('negative','negativeTestCases')):
            rows=per_server.get(key,[])
            for case in rows if isinstance(rows,list) else []:
                if isinstance(case,dict):review_cases.append(dict(case,kind=kind,server=server,origin='Observed server review definition; execution not established'))
    publisher=obj(manifest.get('author'))
    ident=re.sub('[^a-z0-9_-]+','-',str(manifest.get('name') or 'loaded-target').lower()).strip('-_')[:64] or 'loaded-target'
    facts = dict(schema_version=1, id=ident, name=str(interface.get('displayName') or manifest.get('name') or 'Loaded target'),
                 source_revision='content-sha256:'+report['content_sha256'], platform='openai', hosts=[],
                 package_sha256=archive_hash, components=features, server={'connection': connection, 'auth': {'mode': auth_mode}, 'declaration_names': sorted(server_specs)},
                 tools=[], cases=[], host_cases=[], source_files=[], permissions='Host file/terminal capabilities are supplied externally; no bundled MCP connection.' if not features['mcp'] else 'Inspect the actual service authorization before execution.',
                 sample_data='No target data executed or retrieved.', account_setup=[], policy={}, publisher={'name':publisher.get('name','Unknown'),'origin':'Manifest observation; legal identity unverified'},
                 release={'version':manifest.get('version'),'handoff_owner':'Creator','portal_actions':'External human handoff'},
                 listing=interface, review_cases=review_cases, requirement_catalog=catalog, requirement_results=result_by_id,
                 audit_observation=observation, audit_inventory=inventory, audit_package_report=report,
                 audit_scope='Loaded-target static preflight; actual host behavior and legal assertions remain separate')
    details = source_details(files,checker)
    facts['source_details'] = details
    facts['tools'] = details['tools']
    facts['components'].update(details['detected'])
    facts['understanding_draft'] = draft_understanding(facts,details)
    return facts


def completed_documents(facts):
    """Populate the thirteen handoff documents from observed facts, including honest N/A."""
    o = facts['audit_observation']
    binding = facts['source_revision']
    common = ('Target: '+str(o['name'])+' '+str(o['version'])+'\n\n'
              'Source revision: `'+binding+'`\n\n'
              'Evidence: `evidence/source-inspection.json` and `evidence/package-check.json`.\n\n')
    mcp = o['components']['mcp']
    if mcp and not o['components']['remote_mcp']:
        demo = ('Remote MCP recording and five-positive/three-negative review-case requirements do not apply to this local-only desktop package. '
                'Test a clean desktop installation and its main local workflows, and retain actual observations. '
                'Organization confirmation and portal submission remain external human handoffs. ')
    elif mcp:
        demo = ('The package supplies this recording reference: `'+str(o['demo_recording_url'])+'`. '
                if o.get('demo_recording_url') else 'The package supplies no demo recording reference. ')
        demo += ('This is synthetic fixture metadata. ' if o.get('synthetic') else 'This is observed package metadata. ')
        demo += 'Playback and access were not checked. Walk through the target’s supplied positive and negative cases and show the actual tools, outputs, authorization boundaries and side effects. Recording and secure reviewer access remain human handoffs. '
    else:
        demo = 'MCP review recording is not applicable to this skills-only target. Demonstrate its declared skill workflows in a supported host and retain the actual observations. '
        if o['name'] == 'prepare-plugin-submission':
            demo += 'For Submission Studio, audit the broken ZIP, desktop stdio and review-prep fixtures; show findings, applicability, source binding and the human handoff. '
    demo += 'Synthetic output does not prove product-host execution.'
    sections = {
      'architecture/assessment.md': ('Architecture assessment',
        f"Observed {o['file_count']} files, {len(o['skill_paths'])} portable skill entrypoint(s), and {len(o['server_names'])} declared MCP server(s). Effective format: {o['package_format']}; classification: {o['component_kind']}.\n\nThe auditor is a preflight meta-tool; the target retains the observed component classification above. Host capabilities carry out authorized local inspection. Optional MCP/UI/commerce rules are applied only to applicable target components.\n\nActual skill entrypoints: "+', '.join(o['skill_paths'])+'.'),
      'security/auth-architecture.md': ('Authentication architecture',
        'No MCP authentication component is declared; OAuth implementation and token tests are not applicable to this target.' if not mcp else 'MCP declarations exist. Authentication discovery, token checks and isolation need actual service evidence; none was executed during this static audit.'),
      'security/authorization-architecture.md': ('Authorization boundaries',
        'The model uses host-authorized file/terminal/account capabilities. A skill description or Read/Write listing capability grants no server authority. Portal operations stay with the creator. No credentials were requested, stored or tested in this audit.'),
      'security/permission-matrix.md': ('Permission matrix',
        '| Surface | Observed declaration | Audit limit |\n| --- | --- | --- |\n| Listing capabilities | '+', '.join(o['declared_host_capabilities'])+' | Presentation, not authorization |\n| MCP service | '+str(len(o['server_names']))+' declarations | No service authority inferred |\n| Portal | Human creator | No upload, attestations or publication |\n\nDependency and semantic secret-content review remain separate from the static package checker.'),
      'submission/listing.md': ('Listing evidence',
        'Observed display name: '+str(o['display_name'])+'. Publisher text: '+str(o['publisher'].get('name','Unknown'))+'. This is not a verified legal identity.\n\nObserved starter prompts:\n\n'+'\n'.join('- '+p for p in (o['starter_prompts'] if isinstance(o['starter_prompts'],list) else [o['starter_prompts']]))+'\n\nThe package checker assessed supplied listing fields. Real workflow activation remains to be observed in the intended host.'),
      'submission/reviewer-access.md': ('Reviewer access handoff',
        ('This skills-only target has no MCP account or service credentials to provide. The creator supplies a clean supported host environment and exercises its declared skill workflows. ' if not mcp else 'The creator must supply an isolated sample account through secure review fields when authentication is required. ')+ 'No passwords, tokens, MFA codes or reviewer secrets belong in this file.'),
      'submission/demo-plan.md': ('Demonstration applicability',
        demo),
      'submission/release-notes.md': ('Assessed release',
        'The loaded source identifies version '+str(o['version'])+'. This audit records its observed contents and does not infer an unobserved changelog. The generated pack is bound to the source digest; changing the package requires relevant checks to be rerun.'),
      'operations/observability.md': ('Per-run observability',
        'The local checker and generator return structured JSON, check statuses and findings. Retain command, exit code and source digest. No server process or monitoring service was started. Captured evidence must exclude credentials and unrelated user data.'),
      'operations/health-checks.md': ('Local health checks',
        'Run check_package.py on the final archive, the Python regression suite, and TypeScript syntax/build checks where dependencies are available. Treat blocked dependency resolution separately from a failed source check. Fixture success measures the preflight workflow, not service uptime or directory eligibility.'),
      'operations/deployment.md': ('Installation and portal handoff',
        ('This target has unresolved package errors. Deliver the findings and inspected source reference to the creator; repair and recheck the package before installation or submission. ' if facts['audit_package_report']['status'] != 'local_checks_passed' else 'Local package checks passed. Deliver the assessed archive and findings to the creator; actual host behavior remains unverified. ')+
        'Installation, organization allowlisting, portal upload, identity confirmation, review and publication are separate externally performed steps. This audit performs none of them. A clean installation test may be supplied through the product-host report contract.'),
      'operations/rollback.md': ('Rollback handoff',
        'Retain the source/archive for assessed version '+str(o['version'])+' and its digest before applying changes. Re-run package checks on a chosen prior release. The creator uses the owning installation or directory process to restore it; this meta-tool does not change publication state.'),
      'operations/incident-response.md': ('Preflight incident handling',
        'Reject unreadable or escaping archives without executing target code. Keep failed and incomplete observations. If a report contains sensitive data, restrict access and redact a copy before sharing. The creator owns operational response and any changes to external installations; no continuing response service is active.'),
    }
    return {p:'# '+title+'\n\n'+common+body+'\n' for p,(title,body) in sections.items()}
