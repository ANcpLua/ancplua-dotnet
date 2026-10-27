"""OpenAI preparation rules. Pure transforms; empty evidence never proves readiness."""
import copy
import hashlib
import json
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

BASE = 'https://developers.openai.com/plugins/'
SOURCES = {
    'package': BASE + 'build/plugins', 'submission': BASE + 'deploy/submission',
    'policy': BASE + 'plugin-guidelines', 'auth': BASE + 'build/auth',
    'testing': BASE + 'deploy/connect-chatgpt', 'review': BASE + 'deploy/app-review',
    'security': BASE + 'guides/security-privacy',
    'protocol': 'https://modelcontextprotocol.io/specification/2026-07-28',
    'sdk': 'https://ts.sdk.modelcontextprotocol.io/v2/',
}
# Suggested engineering checks, not invented official clause identifiers.
CHECKS = [
    ('architecture', 'Inspect source, operations, components, data and intended hosts', 'package'),
    ('package', 'Inspect the finished archive and effective configuration', 'package'),
    ('protocol', 'Observe actual modern negotiation and requested capabilities', 'protocol'),
    ('tools', 'Execute each exposed tool and verify result, errors and effects', 'testing'),
    ('auth', 'Test discovery, permission boundaries, denial and credential lifecycle', 'auth'),
    ('security', 'Test data isolation, injection boundaries and secret handling', 'security'),
    ('skills', 'Load packaged skills and evaluate realistic tasks', 'testing'),
    ('ui', 'Exercise optional UI in each claimed host', 'testing'),
    ('review', 'Verify applicable review cases on intended product surfaces', 'review'),
    ('listing', 'Prepare accurate listing, publisher facts and real demo evidence', 'submission'),
    ('maintenance', 'Prepare rollout, rollback, observability and regression work', 'submission'),
]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def official_url(url):
    parsed = urlsplit(url)
    return (parsed.scheme == 'https' and parsed.netloc == 'developers.openai.com'
            and not parsed.query and not parsed.fragment
            and (parsed.path.startswith('/plugins/') or parsed.path in (
                '/plugins', '/api/docs/guides/tools-connectors-mcp',
                '/api/docs/guides/evaluation-best-practices')))


def canonical_url(url):
    url = url.rstrip('/')
    return url[:-3] if url.endswith('.md') else url


class _Article(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'nav', 'aside', 'footer', 'header'):
            self.hidden += 1
        if not self.hidden and tag in ('p', 'div', 'li', 'tr', 'br', 'pre', 'h1', 'h2', 'h3', 'h4'):
            self.parts.append('\n' + ('#' * int(tag[1]) + ' ' if re.fullmatch('h[1-4]', tag) else ''))
        if not self.hidden and tag in ('td', 'th'):
            self.parts.append(' | ')

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'nav', 'aside', 'footer', 'header') and self.hidden:
            self.hidden -= 1
        if not self.hidden and tag in ('p', 'div', 'li', 'tr', 'pre', 'h1', 'h2', 'h3', 'h4'):
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def article_text(body):
    """Normalize official representations, retaining headings and table rows."""
    if re.search(r'<(?:html|main|article)\b', body, re.I):
        main = re.search(r'<main\b[^>]*>(.*?)</main>', body, re.I | re.S)
        parser = _Article(); parser.feed(main.group(1) if main else body)
        body = ''.join(parser.parts)
    return '\n'.join(line for row in body.splitlines() if (line := re.sub(r'[ \t]+', ' ', row).strip()))


def discover_pages(index):
    pages = {}
    for title, url in re.findall(r'\[([^\]]+)\]\((https://[^)\s]+)\)', index):
        url = canonical_url(url)
        if official_url(url) and not url.endswith(('.txt', '.json')):
            pages[url] = title
    return pages


def select_documents(features, registry, index=''):
    """Positive capability evidence selects specialized pages; unknown is not true."""
    discovered = discover_pages(index)
    selected = []
    for original in registry['sources']:
        row = copy.deepcopy(original)
        predicates = row['when_any']
        if not any(p == 'always' or features.get(p) is True for p in predicates):
            continue
        url = row['primary_url']
        if url not in discovered and row.get('title'):
            matches = [u for u, title in discovered.items() if title.casefold() == row['title'].casefold()]
            if len(matches) == 1: url = matches[0]
        row.update(primary_url=url, discovered_title=discovered.get(url, row.get('title', row['id'])))
        selected.append(row)
    known = {canonical_url(r['primary_url']) for r in registry['sources']}
    known.update(r['primary_url'] for r in selected)
    for url, title in discovered.items():
        if url in known or re.search('conversion-spec|checkout|reservation|request-quote', url): continue
        topic = 'ui' if re.search(r'\bUI\b', title) else 'mcp' if 'MCP' in title else 'skills' if 'skill' in title.lower() else 'always'
        if topic != 'always' and features.get(topic) is not True: continue
        selected.append(dict(id='discovered.'+digest(url)[:12], domain='Discovered', primary_url=url,
                             when_any=[topic], requires_detected_activity=False, discovered_title=title))
    return selected


def active_export(text, features):
    """The full export is retrieval data; conditional chapters stay inactive."""
    conditional = {'local-services-request-quote-conversion-spec|local services.*(?:get )?quote': 'local_services_quote',
                   'product-checkout-conversion-spec|product checkout conversion': 'product_checkout',
                   'restaurant-reservation-conversion-spec|restaurant reservation.*(?:spec|conversion)': 'restaurant_reservation'}
    chunks = re.split(r'(?=^# )', text, flags=re.M)
    return '\n'.join(c.strip('\n') for c in chunks if c.strip() and not any(re.search(pattern,c[:500],re.I) and features.get(key) is not True
                      for pattern, key in conditional.items()))


def index_document(record, text):
    sections = []; heading = record.get('title', record['id']); lines = []; start = 0
    def flush():
        if lines: sections.append(dict(heading=heading, start=start, text='\n'.join(lines)))
    for n, line in enumerate(text.splitlines()):
        if line.startswith('#'):
            flush(); heading = line.lstrip('# ').strip(); lines = []; start = n
        lines.append(line)
        if sum(map(len, lines)) > 2400:
            flush(); lines = []; start = n+1
    flush()
    return sections


def search_documents(records, query, limit=5):
    terms = set(re.findall(r'[a-z0-9_]+', query.lower())); hits = []
    for doc in records:
        for section in doc.get('sections', []):
            words = set(re.findall(r'[a-z0-9_]+', section['text'].lower()))
            score = len(terms & words) + 2*len(terms & set(section['heading'].lower().split()))
            if score: hits.append(dict(source_id=doc['id'], url=doc['url'], sha256=doc['sha256'],
                                       role=doc['role'], status=doc['status'], score=score, **section))
    return sorted(hits, key=lambda h: (-h['score'], h['source_id']))[:limit]


def rule_candidates(records):
    """Extract source spans, not speculative failures. Execution is a separate step."""
    rows = []
    for doc in records:
        if doc.get('role') != 'primary' or doc.get('status') != 'current': continue
        for section in doc.get('sections', []):
            for sentence in re.split(r'(?<=[.!?])\s+|\n', section['text']):
                if not re.search(r'\b(must|required|cannot|at most|should|need to)\b', sentence, re.I): continue
                if len(sentence) > 1400 or len(sentence) < 15: continue
                rows.append(dict(id='live-'+digest([doc['id'], sentence])[:16], source_id=doc['id'],
                    source_url=doc['url'], source_sha256=doc['sha256'], source_checked_at=doc['validated_at'],
                    heading=section['heading'], quote=sentence, classification='official_guidance',
                    status='Not run', observed_result='Retrieved source guidance; no target failure inferred.', evidence=[]))
    return rows


def advisory_text(quote):
    first=re.split(r'(?<=[.!?])\s+',quote,maxsplit=1)[0]
    advice=re.search(r'\b(should|recommend(?:ed|ation)?|suggest(?:ed|ion)?|optional|example|could|may)\b',first,re.I)
    obligation=re.search(r'\b(must|required|requires?|cannot|need to|do not|will not be accepted)\b',first,re.I)
    return bool(advice and not obligation)


def validate_rule(rule, documents):
    """A sourced rule needs a real current primary span. It never validates its own verdict."""
    doc = next((d for d in documents if d['id'] == rule.get('source_id')), None)
    if not doc or doc.get('role') != 'primary' or doc.get('status') != 'current':
        raise ValueError('Official finding needs an available current primary document')
    if doc['sha256'] != rule.get('source_sha256'):
        raise ValueError('Official finding refers to an obsolete document')
    quote = rule.get('quote', '')
    if len(quote) < 15 or quote not in '\n'.join(s['text'] for s in doc['sections']):
        raise ValueError('Official finding must quote an exact supporting primary span')
    # Validate provenance here; the independent reviewer assesses the obligation
    # in context. A fixed verb list would reject ordinary official imperatives.
    if rule.get('classification') == 'official_requirement' and advisory_text(quote):
        raise ValueError('Guidance cannot be promoted to a mandatory official rule')
    return doc


def policy_context(documents):
    """Conservative typed constraints; never guess a numeric limit from model memory."""
    constraints = []
    aliases = {'displayName':r'display\s*name', 'shortDescription':r'short\s*description',
               'longDescription':r'long\s*description', 'developerName':r'developer\s*name'}
    numbers=r'one|two|three|four|five|six|seven|eight|nine|ten|\d+'
    for doc in documents:
        if doc.get('role') != 'primary' or doc.get('status') != 'current': continue
        for section in doc.get('sections', []):
            for line in section['text'].splitlines():
                for field, alias in aliases.items():
                    if not re.search(alias, line, re.I): continue
                    if line.startswith('|'):
                        subject=line.strip('|').split('|')[0].strip(' `')
                        if not re.fullmatch(alias,subject,re.I):continue
                    match = re.search(r'(?:at most|maximum(?: of)?|up to|no more than|limit(?: of)?|<=|≤)\s*(\d[\d,]*)\s*(?:characters|chars)\b', line, re.I)
                    if not match:match=re.search(r'(\d[\d,]*)\s*characters?\s+or fewer',line,re.I)
                    required=bool(re.search(r'\brequired\b',line,re.I))
                    if not match and not required: continue
                    constraints.append(dict(id='limit-'+digest([doc['id'],line,field])[:12], field=field,
                        maximum=int(match[1].replace(',','')) if match else None,required=required,
                        source_id=doc['id'], source_url=doc['url'], source_sha256=doc['sha256'],
                        source_checked_at=doc['validated_at'], heading=section['heading'], quote=line,
                        classification='official_guidance' if advisory_text(line) else 'official_requirement'))
                if doc['id'] in ('publication.submission','review.remote'):
                    for kind in ('positive','negative'):
                        found=re.search(r'\b('+numbers+r')\s+'+kind+r'\s+(?:and\s+(?:'+numbers+r')\s+(?:positive|negative)\s+)?(?:test\s+)?cases?\b',line,re.I)
                        if found:
                            nums={v:n for n,v in enumerate(('zero','one','two','three','four','five','six','seven','eight','nine','ten'))}
                            number=nums.get(found[1].lower(),int(found[1]) if found[1].isdigit() else 0)
                            constraints.append(dict(id='cases-'+digest([doc['id'],line,kind])[:12],field='review.'+kind,count=number,
                                source_id=doc['id'],source_url=doc['url'],source_sha256=doc['sha256'],source_checked_at=doc['validated_at'],
                                heading=section['heading'],quote=line,classification='official_guidance' if advisory_text(line) else 'official_requirement'))
    return dict(documents=[{k:v for k,v in d.items() if k not in ('sections',)} for d in documents], constraints=constraints)


def policy_findings(context, listing, review=None, remote=False, servers=None):
    findings = []
    def obj(value):return value if isinstance(value,dict) else {}
    review_groups=[('review',obj(obj(review).get('test_cases')))]
    if servers:
        review_groups=[]
        for name,spec in servers.items():
            if not isinstance(spec,dict) or 'url' not in spec:continue
            per_server=obj(obj(obj(spec.get('extensions')).get('com.openai')).get('review'))
            if per_server:
                cases={'positive':per_server.get('testCases'),'negative':per_server.get('negativeTestCases')}
            elif len(servers)==1:cases=obj(obj(review).get('test_cases'))
            else:cases={}
            review_groups.append(('mcpServers.'+name+'.review',cases))
    for rule in context.get('constraints', []):
        if rule['field'].startswith('review.'):
            if not remote:continue
            kind=rule['field'].split('.')[1]
            for path,cases in review_groups:
                value=cases.get(kind,[])
                if not isinstance(value,list) or len(value)!=rule['count']:
                    findings.append(dict(rule,id=rule['id']+'-'+digest(path)[:8],code='live_review_count',path=path+'.'+kind,
                        severity='error' if rule['classification']=='official_requirement' else 'warning',
                        observed_result=f'Observed {len(value) if isinstance(value,list) else "invalid"} declared {kind} cases.',
                        fix=f"Supply {rule['count']} {kind} review cases from the current source.",status='Failed'))
            continue
        else:
            value=listing.get(rule['field']);limit=rule.get('maximum')
            failed=(rule.get('required') and (not isinstance(value,str) or not value.strip())) or (isinstance(value,str) and limit is not None and len(value)>limit)
            message=(f"Provide {rule['field']}." if not value else f"Shorten {rule['field']} to {limit} characters.")
        if failed:
            findings.append(dict(rule, code='live_text_limit', path='interface.'+rule['field'],
                severity='error' if rule['classification']=='official_requirement' else 'warning',
                observed_result=f"Observed value does not satisfy the retrieved constraint: {value!r}.",
                fix=message,status='Failed'))
    return findings


def binding(facts):
    def digest(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    if facts.get('retained_execution_binding'):
        return copy.deepcopy(facts['retained_execution_binding'])
    execution = {k:facts.get(k) for k in ('id','source_revision','package_sha256','tools','server','hosts','host_cases','cases')}
    return dict(integration_id=facts['id'], source_revision=facts['source_revision'],
                input_sha256=digest(execution if facts.get('workflow_schema_version')==2 else facts), inventory_sha256=digest(facts.get('tools', [])))


def requirements(facts):
    if facts.get('workflow_schema_version') == 2:
        return [dict(requirement_id=r['id'], platform='openai', domain='Live documentation',
            classification=r['classification'], applicability='Selected source capability',
            summary=r['quote'], source_url=r['source_url'], source_checked_at=r['source_checked_at'],
            source_revision=r['source_sha256'], implementation_revision=facts['source_revision'],
            verification='Current primary span; independent assessment and execution remain separate',
            status=r.get('status','Not run'),observed_result=r.get('observed_result','Retrieved guidance; no failure inferred'),
            evidence=r.get('evidence',[])) for r in facts.get('active_rules',[])]
    catalog = facts.get('requirement_catalog', [])
    results = facts.get('requirement_results', {})
    if not catalog:
        return []  # The I/O layer loads the versioned catalog; no invented completed records.
    rows = []
    for entry in catalog:
        result = results.get(entry['id'], {})
        rows.append(dict(requirement_id=entry['id'], platform='openai', domain=entry['domain'],
                         classification=entry['classification'], applicability=entry['scope'],
                         summary=entry['summary'], source_url=entry['source_url'],
                         source_checked_at=entry['source_checked_at'], source_revision=None,
                         implementation_revision=facts['source_revision'],
                         protocol_version='2026-07-28' if entry['scope'] in ('mcp','events') else None,
                         transport=facts.get('server', {}).get('connection', {}).get('transport'),
                         verification=entry['verification'], status=result.get('status','Not run'),
                         observed_result=result.get('observed_result','No loaded-target observation; initialization is expected.'),
                         evidence=result.get('evidence', []), meta_tool_support=entry['meta_tool_support'],
                         implementation=entry['implementation'], validation_fixture=entry['validation_fixture']))
    return rows



def readiness(facts, plan):
    findings = []
    server = facts.get('server', {})
    skills_only = facts.get('components', {}).get('mcp') is False and not server.get('connection')
    if facts['source_revision'] == 'UNRECORDED':
        findings.append(dict(code='source_revision_missing', status='Blocked', message='Record actual revision or source digest.'))
    if not facts.get('hosts') and not facts.get('audit_observation'):
        findings.append(dict(code='hosts_missing', status='Blocked', message='Declare intended OpenAI product/API surfaces.'))
    if not skills_only and not server.get('connection'):
        findings.append(dict(code='connection_unknown', status='Blocked', message='Inspect MCP declarations or explicitly record components.mcp: false.'))
    if server.get('connection', {}).get('transport') == 'sse':
        findings.append(dict(code='legacy_transport', status='Blocked', message='Migrate legacy SSE to a modern supported transport and test negotiation.'))
    return dict(binding=binding(facts), platform='openai', sources=SOURCES,
                source_dates='Check each requirement individually; inventory URLs are not retrieval evidence.',
                findings=findings, requirements=requirements(facts),
                readiness=('Locally validated' if facts.get('audit_package_report',{}).get('status') == 'local_checks_passed' else 'Preflight findings recorded') if facts.get('audit_observation') else 'Not verified',
                live_verification_performed=False,
                auth_checks=[dict(check=k, status='Not applicable' if skills_only else 'Not run', evidence=[])
                             for k in ('discovery', 'registration', 'pkce', 'redirects', 'audience', 'scopes', 'expiry', 'refresh', 'denial', 'revocation', 'tenant_isolation')],
                host_checks=[dict(host=h, status='Not run', evidence=[]) for h in facts.get('hosts', [])],
                next_actions=[f['message'] for f in findings] + ['Implement and run applicable tests; keep product-host evidence separate.'])


def policy_matrix(facts):
    return dict(binding=binding(facts), platform='openai', source=SOURCES['policy'],
                source_checked_at=next((r['source_checked_at'] for r in facts.get('requirement_catalog',[]) if r['source_url']==SOURCES['policy']),None), requirements=requirements(facts),
                preparation_complete=False, legal_compliance_certified=False,
                decisions=copy.deepcopy(facts.get('policy', {})))


def obligations(facts):
    return dict(binding=binding(facts), platform='openai', source=SOURCES['submission'],
                source_checked_at=next((r['source_checked_at'] for r in facts.get('requirement_catalog',[]) if r['source_url']==SOURCES['submission']),None), publisher=copy.deepcopy(facts.get('publisher', {})),
                required_creator_facts=['legal identity', 'rights', 'actual data practices', 'support', 'reviewer access'],
                preparation_complete=False, terms_accepted_by_tool=False, submission_performed=False)


def release_plan(facts, plan):
    return dict(binding=binding(facts), platform='openai', source=SOURCES['submission'],
                source_checked_at=next((r['source_checked_at'] for r in facts.get('requirement_catalog',[]) if r['source_url']==SOURCES['submission']),None), current_and_proposed=copy.deepcopy(facts.get('release', {})),
                actions=dict(server='Deploy and exercise actual endpoint using its owning deployment process.',
                             package='Build and validate changed skills/metadata in a new version; preserve existing identity.',
                             listing='Read current portal guidance; track draft, review, approval and publication separately.'),
                regression_case_ids=[c['id'] for c in plan['cases']],
                rollout='Supply actual deployment components and owner.', rollback='Supply a tested recovery procedure.',
                ready_for_owner_review=False, deployment_performed=False, continuous_monitoring_configured=False)


def handoff_records(facts, plan):
    """Output path -> JSON object; distinguish inspection from unexecuted behavior."""
    observed = facts.get('audit_observation')
    evidence = ['evidence/source-inspection.json', 'evidence/package-check.json'] if observed else []
    base = dict(binding=binding(facts), status='Not run', evidence=evidence)
    if observed:
        base.update(observed_result='Inspected target definitions; behavior and external actions were not executed.',
                    source_revision=facts['source_revision'])
    def record(**kwargs):
        return {**copy.deepcopy(base), **kwargs}
    mc = facts.get('components', {}).get('mcp')
    state = 'Not applicable' if mc is False and not facts.get('server', {}).get('connection') else 'Not run'
    review_state = 'Not applicable' if state == 'Not applicable' or (observed and not facts['components'].get('remote_mcp')) else 'Not run'
    protocol = dict(protocol_version='2026-07-28', requested_era='modern', observed_era=None,
                    implementation_revision=facts['source_revision'], status=state, evidence=evidence,
                    observed_result='No MCP component declared; wire protocol is inapplicable.' if state == 'Not applicable' else 'Protocol negotiation not executed.')
    tools = facts.get('tools', [])
    records = {
        'architecture/components.json': record(supplied=facts.get('components', {}), status='Observed' if observed else 'Not run'),
        'architecture/tool-inventory.json': record(supplied_tools=tools),
        'architecture/host-matrix.json': record(hosts=[dict(host=h, status='Not run', evidence=[]) for h in facts.get('hosts', [])]),
        'readiness/requirements.json': record(requirements=requirements(facts)),
        'protocol/supported-versions.json': dict(protocol, claimed_versions=[]),
        'protocol/capability-matrix.json': dict(protocol, supplied_capabilities=facts.get('server', {}).get('required_capabilities', [])),
        'protocol/compatibility-tests.json': dict(protocol, cases=[]),
        'protocol/negotiation-results.json': dict(protocol, observations=[]),
        'tools/inventory.json': record(supplied_tools=tools, status=state),
        'tools/schemas.json': record(status=state, schemas=[{k: t[k] for k in ('name', 'inputSchema', 'outputSchema') if k in t} for t in tools]),
        'tools/cases.json': record(cases=plan['cases'], status=state), 'tools/results.json': record(results=[], status=state),
        'tools/coverage.json': record(status=state, tools=[dict(name=t['name'], status='Not run') for t in tools]),
        'security/access-matrix.json': record(permissions=facts.get('permissions', 'Unknown')),
        'security/scopes.json': record(scopes=[], status=state), 'security/oauth-cases.json': record(cases=[], status=state),
        'security/authorization-results.json': record(results=[], status=state),
        'submission/metadata.json': record(supplied=facts.get('listing', {}), status='Observed' if observed else 'Not run'),
        'submission/review-cases.json': record(cases=facts.get('review_cases',[]), status=review_state, note='Remote MCP review cases apply only to a declared remote target; retained cases are definitions, not execution evidence.'),
        'submission/publication-state.json': record(lifecycle='Prepared', submitted=False, approved=False, published=False),
        'publisher/facts.json': record(supplied=facts.get('publisher', {}), creator_confirmed=False),
        'testing/inspector/commands.json': record(commands=[]), 'testing/inspector/results.json': record(results=[]),
        'testing/mcpdo/commands.json': record(commands=[]), 'testing/mcpdo/results.json': record(results=[]),
        'operations/plan.json': record(monitoring_active=False, supplied=facts.get('release', {})),
    }
    if facts.get('workflow_schema_version')==2:
        records.update({'submission/understanding.json':record(draft=facts.get('understanding_draft'),status='Inferred'),
            'submission/choices.json':record(choices=facts.get('confirmed_choices'),status='Creator selected' if facts.get('confirmed_choices',{}).get('confirmed') else 'Inferred'),
            'submission/listing-draft.json':record(interface=facts.get('listing_draft'),status='Draft'),
            'evidence/documentation.json':record(snapshot=facts.get('documentation_snapshot'),status='Retrieved with recorded gaps')})
    return records
