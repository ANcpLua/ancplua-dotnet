#!/usr/bin/env python3
"""Persistent conversational wizard adapter. Never operates a submission portal."""
import argparse
from contextlib import contextmanager
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import uuid
import zipfile
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, quote, unquote

import audit_target
import check_package
import host_reports
import prepare_workflow
import wizard_core as core
import openai_core as policy

HERE = Path(__file__).resolve().parent


class _Redirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, url):
        old, new = urlsplit(req.full_url), urlsplit(url)
        allowed = {'developers.openai.com'} if old.hostname=='developers.openai.com' else {'api.github.com','github.com','codeload.github.com'}
        if new.scheme!='https' or new.hostname not in allowed or new.username or new.password:
            raise ValueError('Refused a redirect outside the selected source provider')
        follow = super().redirect_request(req,fp,code,msg,headers,url)
        if old.hostname != new.hostname: follow.remove_header('Authorization')
        return follow


def fetch_url(url, previous=None, github=False):
    """Bounded HTTP adapter. Tests inject responses; targets cannot choose policy hosts."""
    parsed = urlsplit(url)
    if not (parsed.scheme=='https' and not parsed.username and not parsed.password and
            (parsed.hostname in {'api.github.com','codeload.github.com'} if github else policy.official_url(url))):
        raise ValueError('Unsupported source URL')
    headers = {'User-Agent':'Submission-Studio/2.3.0','Accept':'application/vnd.github+json' if github else 'text/html,text/plain,text/markdown'}
    if github and parsed.hostname=='api.github.com' and os.environ.get('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer '+os.environ['GITHUB_TOKEN']
    if previous:
        if previous.get('etag'): headers['If-None-Match']=previous['etag']
        if previous.get('last_modified'): headers['If-Modified-Since']=previous['last_modified']
    try:
        with build_opener(_Redirect()).open(Request(url,headers=headers),timeout=15) as response:
            limit = check_package.TOTAL_LIMIT if github else 16*1024*1024
            body = response.read(limit+1)
            if len(body)>limit: raise ValueError('Source exceeds the bounded retrieval limit')
            return dict(status=response.status,body=body,url=response.url,
                        etag=response.headers.get('ETag'),last_modified=response.headers.get('Last-Modified'))
    except HTTPError as exc:
        if exc.code==304 and previous: return dict(status=304,url=url,body=b'')
        raise ValueError('Source retrieval returned HTTP '+str(exc.code)) from exc
    except (URLError,TimeoutError,OSError) as exc:
        raise ValueError('Source retrieval unavailable: '+type(exc).__name__) from exc


def acquire_source(locator, work, ref=None, plugin_root=None):
    """Pin GitHub input or inspect local input, then resolve a plugin subtree."""
    origin = dict(kind='local',locator=str(locator),visibility='unknown')
    if str(locator).startswith('https://'):
        parsed=urlsplit(str(locator)); parts=parsed.path.strip('/').split('/')
        if parsed.netloc!='github.com' or len(parts)<2 or parsed.query or parsed.fragment or parsed.username:
            raise ValueError('Provide a GitHub repository URL or a local folder/ZIP')
        owner,repo=parts[:2];repo=repo.removesuffix('.git')
        if not all(re.fullmatch(r'[\w.-]+',p) for p in (owner,repo)): raise ValueError('Invalid GitHub repository path')
        api='https://api.github.com/repos/'+owner+'/'+repo
        metadata=json.loads(fetch_url(api,github=True)['body'])
        suffix=parts[2:]
        if suffix and suffix[0]!='tree': raise ValueError('Use a repository/tree URL, not a file URL')
        if suffix and not ref:
            ref=unquote(suffix[1]) if len(suffix)>1 else None
            if len(suffix)>2 and plugin_root is None: plugin_root='/'.join(map(unquote,suffix[2:]))
        selected_ref=ref or metadata['default_branch']
        commit=json.loads(fetch_url(api+'/commits/'+quote(selected_ref,safe=''),github=True)['body'])['sha']
        if not re.fullmatch('[0-9a-f]{40}',commit): raise ValueError('GitHub returned an invalid pinned revision')
        folder=work/'sources';folder.mkdir(parents=True,exist_ok=True)
        source=folder/(owner+'-'+repo+'-'+commit+'.zip')
        receipt=source.with_suffix('.sha256')
        if source.is_symlink() or receipt.is_symlink():raise ValueError('Repository cache must not use symbolic links')
        if source.exists() and receipt.exists():
            if file_sha(source)!=receipt.read_text().strip():raise ValueError('Cached repository archive changed')
        else:
            source.write_bytes(fetch_url(api+'/zipball/'+commit,github=True)['body']);receipt.write_text(file_sha(source)+'\n')
        origin=dict(kind='github',locator='https://github.com/'+owner+'/'+repo,ref=selected_ref,commit=commit,
                    visibility='private' if metadata.get('private') else 'public',provider='GitHub API',retrieved_at=now())
    else:
        source=Path(locator).resolve()
        if not source.exists(): raise ValueError('The selected local source does not exist')
    files=check_package.load_files(source)
    roots=audit_target.plugin_roots(files)
    if plugin_root is None and len(roots)>1:
        return dict(path=str(source),origin=origin,roots=roots)
    root=plugin_root if plugin_root is not None else roots[0]
    if root and not check_package.safe_path(root): raise ValueError('Plugin root must be a contained relative directory')
    if root and root not in roots: raise ValueError('Choose an observed plugin root')
    origin['plugin_root']=root
    if not root: return dict(path=str(source),origin=origin,roots=[])
    if source.is_dir(): return dict(path=str(source/root),origin=origin,roots=[])
    selected={name[len(root)+1:]:data for name,data in files.items() if name.startswith(root+'/')}
    out=work/'sources'/('plugin-'+policy.digest([origin,root])+'.zip');out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(selected.items()):
            info=zipfile.ZipInfo(name);info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(files.modes.get(root+'/'+name,0o100644))<<16
            archive.writestr(info,data)
    return dict(path=str(out),origin=origin,roots=[])


def document_records(state, work):
    records=[]
    for saved in state.get('docs',{}).get('documents',[]):
        row=copy.deepcopy(saved)
        if row.get('file'):
            path=Path(row['file'])
            if (work/'docs').resolve() not in path.resolve().parents or path.is_symlink() or file_sha(path)!=row['sha256']:
                raise ValueError('Saved official-document content changed or escaped its workspace')
            text=path.read_text();row['text']=text;row['sections']=policy.index_document(row,text)
        else: row['sections']=[]
        records.append(row)
    return records


def sync_documents(state, work, supplied=None, offline=False, fetch=fetch_url):
    """Live official discovery/indexing and primary checks; retrieval gaps are not project defects."""
    state=copy.deepcopy(state); registry=read_json(HERE.parent/'references/official-docs-sources.json')
    old={d['id']:d for d in document_records(state,work)}; prior=state.get('docs',{})
    provided={canonical['url']:canonical for canonical in supplied.get('documents',[])} if supplied else {}
    if supplied and supplied.get('origin')=='synthetic' and not state['synthetic']:
        raise ValueError('Synthetic documentation cannot establish current policy in a real session')
    def retrieve(ident,url,role):
        before=old.get(ident);status='unavailable';error=None;headers={}
        try:
            if url in provided:
                incoming=provided[url]
                if not incoming.get('observed_at') or not incoming.get('provider'):raise ValueError('Imported docs need a provider and actual observation time')
                text=incoming['text'];headers={};provider=incoming['provider']
                status='synthetic' if supplied.get('origin')=='synthetic' else 'current'
                checked=incoming['observed_at']
            elif offline: raise ValueError('Offline mode; current page not retrieved')
            else:
                response=fetch(url,before)
                if response['status']==304 and before: text=before['text']
                else:
                    body=response['body'].decode('utf-8')
                    text=policy.article_text(body) if role=='primary' else body
                headers=response;provider='http';status='current';checked=now()
            if len(text.encode())>16*1024*1024 or not text.strip():raise ValueError('Empty or oversized official document')
            if role=='export': text=policy.active_export(text,state['snapshot']['features'])
            sha=hashlib.sha256(text.encode()).hexdigest();path=work/'docs'/(sha+'.txt');path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            if path.is_symlink(): raise ValueError('Document destination is a symbolic link')
            path.write_text(text)
            return dict(id=ident,url=url,role=role,status=status,validated_at=checked,sha256=sha,file=str(path),
                        requested_url=url,resolved_url=headers.get('url',url),provider=provider,etag=headers.get('etag',before.get('etag') if before else None),
                        last_modified=headers.get('last_modified',before.get('last_modified') if before else None))
        except (ValueError,UnicodeError,KeyError) as exc:
            error=str(exc)
        if before:
            return {k:v for k,v in dict(before,status='cached-unverified',error=error).items() if k not in ('text','sections')}
        return dict(id=ident,url=url,role=role,status=status,error=error)
    with ThreadPoolExecutor(max_workers=6) as pool:
        discovery=list(pool.map(lambda args:retrieve(*args),[('index',registry['discovery_index'],'index'),('export',registry['combined_export'],'export')]))
    index=next((Path(d['file']).read_text() for d in discovery if d['id']=='index' and d.get('file')),'')
    selected=policy.select_documents(state['snapshot']['features'],registry,index)
    with ThreadPoolExecutor(max_workers=6) as pool:
        primary=list(pool.map(lambda s:retrieve(s['id'],s['primary_url'],'primary'),selected))
    documents=discovery+primary
    changed=[d['id'] for d in documents if d.get('sha256')!=old.get(d['id'],{}).get('sha256') or d.get('status')!=old.get(d['id'],{}).get('status')]
    state['docs']=dict(documents=documents,selected_ids=[d['id'] for d in primary],synced_at=now(),
        mode='offline' if offline else 'supplied' if supplied else 'live',
        content_sha256=policy.digest([(d['id'],d.get('sha256')) for d in documents]),
        gaps=[dict(id=d['id'],url=d['url'],reason=d.get('error',d['status'])) for d in documents if d['status']!='current'])
    if changed:
        state['findings']=[f for f in state.get('findings',[]) if f.get('source_id') not in changed]
        if any(d['id'] in changed and d['role']=='primary' for d in documents):
            previous=state.get('jobs',{}).pop('independent-review',None)
            if previous:state=core.event(state,'review-policy-refresh',{'previous_review':previous,'changed_documents':changed},now())
        state=core.event(state,'docs-synchronized',dict(changed_ids=changed,gaps=len(state['docs']['gaps'])),now())
    return state


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError('Use a regular JSON file below 8 MiB')
    return json.loads(path.read_text(), object_pairs_hook=check_package.no_duplicates)


def write_json(path, value):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Refuse to overwrite a symbolic link')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix='.wizard-')
    try:
        with os.fdopen(fd, 'w') as out:
            json.dump(value, out, indent=2); out.write('\n')
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def file_sha(path):
    sha = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            sha.update(block)
    return sha.hexdigest()


def outside(path, source):
    if source is None:
        return
    path, source = Path(path).resolve(), Path(source).resolve()
    if path == source or (source.is_dir() and source in path.parents):
        raise ValueError('Store the session and generated artifacts outside the inspected target')


@contextmanager
def session_lock(path):
    lock = path.with_name(path.name + '.lock')
    if lock.is_symlink():
        raise ValueError('Session lock must not be a symbolic link')
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('a+b') as stream:
        if os.name == 'nt':
            import msvcrt
            stream.seek(0); stream.write(b'0'); stream.flush(); stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise ValueError('Session is in use; retry after the other operation finishes') from exc
        else:
            import fcntl
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise ValueError('Session is in use; retry after the other operation finishes') from exc
        try:
            yield
        finally:
            if os.name == 'nt':
                stream.seek(0); msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def freeze(source, files, work):
    folder = work / 'archives'; folder.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=folder, suffix='.zip'); os.close(fd)
    temp = Path(temp)
    try:
        if source.is_file():
            if source.stat().st_size > check_package.TOTAL_LIMIT:
                raise ValueError('Archive exceeds the bounded checker limit')
            shutil.copyfile(source, temp)
        else:
            with zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as archive:
                for name, data in sorted(files.items()):
                    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    executable = source.joinpath(*Path(name).parts).stat().st_mode & 0o111
                    info.external_attr = (0o100755 if executable else 0o100644) << 16
                    archive.writestr(info, data)
        sha = file_sha(temp); destination = folder / (sha + '.zip')
        if destination.exists():
            if destination.is_symlink() or file_sha(destination) != sha:
                raise ValueError('Frozen archive changed; restore its bytes before continuing')
        else:
            os.replace(temp, destination)
        return destination, sha
    finally:
        temp.unlink(missing_ok=True)


def observe(state, session, work):
    if not state.get('source_path'):
        return state
    source = Path(state['source_path']).resolve()
    outside(session, source); outside(work, source)
    files = check_package.load_files(source)
    probe = check_package.Checker(files, 'openai', 'package'); probe.run()
    local = any(isinstance(s, dict) and 'command' in s for s in probe.servers.values())
    route = 'desktop-only' if local else 'remote'
    profile = 'submission' if state['answers'].get('goal', {}).get('goal') == 'public-submission' else 'package'
    archive, sha = freeze(source, files, work)
    catalog = read_json(HERE.parent / 'references/requirements.json')['requirements']
    context=policy.policy_context(document_records(state,work))
    facts = audit_target.inspect_target(archive, catalog, submission_route=route,
        allowlist=state['answers'].get('allowlist'), synthetic=state['synthetic'], profile=profile,rule_context=context)
    features = dict(facts['components'], local_mcp=local, remote_mcp=probe.remote_review)
    snapshot = dict(content_sha256=facts['audit_package_report']['content_sha256'], package_sha256=sha,
        archive=str(archive), name=facts['id'], version=facts['audit_observation']['version'],
        route=route, features=features, package_report=facts['audit_package_report'], facts=facts,
        review_cases=facts['review_cases'], demo_recording_url=facts['audit_observation'].get('demo_recording_url'))
    refreshed = core.with_snapshot(state, snapshot, str(source), now())
    if state['answers'].get('allowlist') and not refreshed['answers'].get('allowlist'):
        return observe(refreshed, session, work)  # Recheck after a changed target invalidates confirmation.
    return refreshed


def prepare_state(state, session, work, refresh_docs=False, supplied_docs=None):
    if not state.get('snapshot'): return state
    state=copy.deepcopy(state)
    state['answers'].setdefault('goal',{'goal':'public-submission'})
    state['answers'].setdefault('hosts',{'hosts':['chatgpt']})
    registry=read_json(HERE.parent/'references/official-docs-sources.json')
    needed={d['id'] for d in policy.select_documents(state['snapshot']['features'],registry)}
    stale=bool(state.get('docs')) and (datetime.now(timezone.utc)-datetime.fromisoformat(state['docs']['synced_at'])).total_seconds()>86400
    if refresh_docs or stale or supplied_docs or not state.get('docs') or not needed.issubset(set(state['docs'].get('selected_ids',[]))):
        state=sync_documents(state,work,supplied_docs,offline=state.get('docs_mode')=='offline')
        state=observe(state,session,work)
    docs=document_records(state,work)
    facts=state['snapshot']['facts']
    facts['workflow_schema_version']=2
    facts['documentation_snapshot']={k:v for k,v in state['docs'].items() if k!='documents'}
    facts['documentation_snapshot']['documents']=[{k:d.get(k) for k in ('id','url','requested_url','resolved_url','role','status','validated_at','sha256','file','provider')} for d in docs]
    facts['active_rules']=policy.rule_candidates(docs)
    if state.get('draft_override',{}).get('content_sha256')==state['snapshot']['content_sha256']:
        state['understanding']=copy.deepcopy(state['draft_override']['draft'])
    facts['understanding_draft']=copy.deepcopy(state['understanding'])
    if state['choices'].get('confirmed') and not state['answers'].get('test-plan') and not state.get('plan_editing'):
        state['answers']['test-plan']={'cases':core.derive_test_plan(state)}
    facts['confirmed_choices']=copy.deepcopy(state['choices'])
    selected=set(state['choices'].get('task_ids',[t['id'] for t in state['understanding']['tasks'] if t.get('supported')]))
    facts['listing_draft']=dict(facts['listing'],longDescription='\n'.join(t['description'] for t in state['understanding']['tasks'] if t['id'] in selected),
        defaultPrompt=[t['direct_prompt'] for t in state['understanding']['tasks'] if t['id'] in selected][:3])
    package_path=work/'jobs'/'package-check.json';write_json(package_path,facts['audit_package_report'])
    state['jobs']['package-check']=dict(status='Completed',outcome=facts['audit_package_report']['status'],report=str(package_path),
        report_sha256=file_sha(package_path),binding=core.binding(state),provider='executed local package checker')
    if state.get('legacy_binding'):
        facts['retained_execution_binding']=state['legacy_binding']
    review=state.get('jobs',{}).get('independent-review')
    if review and (review.get('binding')!=core.binding(state) or review.get('docs_sha256')!=state['docs']['content_sha256']):
        state=core.event(state,'review-inputs-changed',{'previous_job':review},now())
        state['jobs'].pop('independent-review',None);state['findings']=[]
        state['answers'].pop('requirement-review',None)
        for key in ('independent-review','requirement-review'):state['deferred'].pop(key,None)
    if (state['choices'].get('confirmed') or state['choices'].get('legacy_retained')) and not state.get('plan_editing') and not state.get('jobs',{}).get('independent-review'):
        request=dict(schema_version=1,kind='independent-review',binding=core.binding(state),
            docs_sha256=state['docs']['content_sha256'],drafter_id=state['actor_id'],
            target_archive=state['snapshot']['archive'],source_origin=state['source_origin'],
            understanding=state['understanding'],choices=state['choices'],
            documentation=facts['documentation_snapshot'],host_cases=state['answers'].get('test-plan',{}).get('cases',[]),
            instruction='Read the pinned source and selected current official documents independently. Check task/implementation/claim alignment, applicable review requirements and concrete submission errors. Return evidence-backed findings and suggested repairs. Do not run a live upload or invent host observations.')
        path=work/'jobs'/'independent-review-request.json';write_json(path,request)
        state['jobs']['independent-review']=dict(id=uuid.uuid4().hex,status='Pending',request=str(path),
            request_sha256=file_sha(path),binding=request['binding'],docs_sha256=request['docs_sha256'])
    return state


def refine_understanding(state, value):
    if value.get('content_sha256')!=state['snapshot']['content_sha256'] or not value.get('provider'):
        raise ValueError('Source synthesis must identify its current target and provider')
    draft=value['draft'];known={f['path'] for f in state['snapshot']['facts']['audit_inventory']}
    if not isinstance(draft.get('summary'),str) or not 1<=len(draft.get('tasks',[]))<=100 or len(draft.get('boundaries',[]))>50:
        raise ValueError('Supply a summary, 1–100 source-derived tasks and at most 50 boundary examples')
    ids=[]
    for task in draft['tasks']:
        if not all(isinstance(task.get(k),str) and task[k].strip() for k in ('id','label','description','direct_prompt','indirect_prompt','expected')):
            raise ValueError('Each inferred task needs meaningful prompts and expected behavior')
        if not task.get('source_paths') or any(p not in known for p in task['source_paths']):
            raise ValueError('Each task must refer to inspected target files')
        ids.append(task['id']);task['provenance']='Host model inference from inspected source; not execution evidence'
    for b in draft.get('boundaries',[]):
        if not all(isinstance(b.get(k),str) and b[k].strip() for k in ('id','label','prompt','expected')):raise ValueError('Boundary examples need ID, label, prompt and expected behavior')
    if len(ids)!=len(set(ids)):raise ValueError('Task IDs must be unique')
    draft.setdefault('claims',[dict(task_id=t['id'],text=t['label']) for t in draft['tasks'] if t.get('supported')])
    if any(c.get('task_id') not in ids for c in draft['claims']):raise ValueError('Listing claims must refer to an inferred task')
    state=copy.deepcopy(state)
    if core.meaning(state['understanding'])!=core.meaning(draft):
        state['choices']={};state['jobs']={};state['host_rows']={}
        for key in core.ORDER[core.ORDER.index('test-plan'):]:state['answers'].pop(key,None)
    state.pop('pending_correction',None)
    state['understanding']=draft;state['draft_override']=dict(content_sha256=value['content_sha256'],draft=draft,provider=value['provider'])
    return core.event(state,'source-synthesis',dict(provider=value['provider'],draft_sha256=core.meaning(draft)),now())


def import_review(state, value, path, work):
    job=state.get('jobs',{}).get('independent-review')
    if not job or value.get('binding')!=core.binding(state) or value.get('docs_sha256')!=state['docs']['content_sha256']:
        raise ValueError('Independent review belongs to a different source, plan or document snapshot')
    if value.get('request_sha256')!=job['request_sha256']:raise ValueError('Review must answer the saved independent request')
    if value.get('status')=='Running':
        if not all(isinstance(value.get(k),str) and value[k].strip() for k in ('provider','job_reference','dispatched_at')):
            raise ValueError('A dispatched review needs its actual provider, job reference and dispatch time')
        if datetime.fromisoformat(value['dispatched_at'].replace('Z','+00:00')).tzinfo is None:
            raise ValueError('Dispatch time needs a timezone')
        state=copy.deepcopy(state)
        state['jobs']['independent-review'].update(status='Running',provider=value['provider'],
            job_reference=value['job_reference'],dispatched_at=value['dispatched_at'])
        return core.event(state,'review-dispatched',{'provider':value['provider'],'job_reference':value['job_reference']},now())
    if value.get('status')=='Unavailable':
        if not value.get('reason'):raise ValueError('Record why the review provider is unavailable')
        state=copy.deepcopy(state);state['jobs']['independent-review'].update(status='Unavailable',reason=value['reason'])
        return core.event(state,'review-unavailable',{'reason':value['reason']},now())
    if not value.get('reviewer_id') or value['reviewer_id']==state['actor_id']:
        raise ValueError('Use an independent reviewer identity, distinct from the draft author')
    if value.get('origin') not in ('observed','synthetic') or (value.get('origin')=='synthetic' and not state['synthetic']):
        raise ValueError('A real session needs an actually observed independent report')
    if not isinstance(value.get('findings'),list) or not value.get('summary') or not value.get('provider'):
        raise ValueError('Review needs provider, summary and concrete findings (an empty list is allowed)')
    evidence=value.get('evidence',{});raw=path.resolve().parent/evidence.get('file','')
    if raw.is_symlink() or path.resolve().parent not in raw.resolve().parents or not raw.is_file() or file_sha(raw)!=evidence.get('sha256'):
        raise ValueError('Attach the actual independent agent output with its SHA-256')
    known={r['path']:r for r in state['snapshot']['facts']['audit_inventory']};docs=document_records(state,work)
    findings=[]
    for row in value['findings']:
        if not all(row.get(k) for k in ('id','message','fix','source_path')) or row['source_path'] not in known:
            raise ValueError('Each finding needs an observed source path and an actionable correction')
        if row.get('classification') in ('official_requirement','official_guidance'):
            current=policy.validate_rule(row,docs)
            row=dict(row,source_url=current['url'],source_checked_at=current['validated_at'])
            if not row.get('applicability') or not row.get('observed_result'):raise ValueError('Official finding needs target applicability and an actual failed observation')
        elif row.get('classification') not in ('engineering_advice','structural_check'):
            raise ValueError('Use an explicit finding classification')
        findings.append(dict(row,severity='error' if row['classification'] in ('official_requirement','structural_check') else 'warning',
                             status='Failed',evidence_sha256=evidence['sha256'],origin=value['origin']))
    folder=work/'jobs'/'reviews'/file_sha(path);folder.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(raw,folder/'agent-output.txt');write_json(folder/'report.json',value)
    state=copy.deepcopy(state);state['findings']=findings
    state['jobs']['independent-review'].update(status='Completed',report=str(folder/'report.json'),
        report_sha256=file_sha(folder/'report.json'),evidence=str(folder/'agent-output.txt'),evidence_sha256=evidence['sha256'],
        reviewer_id=value['reviewer_id'],provider=value['provider'],origin=value['origin'])
    return core.event(state,'independent-review-recorded',dict(reviewer_id=value['reviewer_id'],findings=len(findings)),now())


def apply_fix(state, value, work):
    """Apply an explicit source-bound replacement set; no shell or implicit target execution."""
    if value.get('content_sha256')!=state['snapshot']['content_sha256']:raise ValueError('Fix was prepared for a different source')
    files=check_package.load_files(Path(state['snapshot']['archive']));changes=value.get('changes',[])
    modes=files.modes
    if not changes:raise ValueError('The prepared fix has no changes')
    seen=set()
    for change in changes:
        name=change.get('path')
        if not check_package.safe_path(name) or name=='.' or str(Path(name))!=name or name in seen:raise ValueError('Use unique contained source paths')
        seen.add(name);before=files.get(name,b'')
        if hashlib.sha256(before).hexdigest()!=change.get('before_sha256'):raise ValueError('Prepared fix has stale source bytes')
        if not isinstance(change.get('replacement'),str) or len(change['replacement'].encode())>check_package.LIMIT:raise ValueError('Use a bounded UTF-8 replacement')
        files[name]=change['replacement'].encode()
    target=work/'repairs'/uuid.uuid4().hex;target.mkdir(parents=True,mode=0o700)
    for name,data in files.items():
        path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        if modes.get(name,0)&0o111:path.chmod(0o755)
    state=copy.deepcopy(state);state['source_path']=str(target)
    return core.event(state,'prepared-fix-applied',dict(paths=sorted(seen),previous_archive=state['snapshot']['archive']),now())


def propose_fix(state, value, work):
    if value.get('content_sha256')!=state['snapshot']['content_sha256'] or not value.get('changes'):
        raise ValueError('A proposed fix needs the current source binding and changes')
    files=check_package.load_files(Path(state['snapshot']['archive']))
    seen=set()
    for change in value['changes']:
        name=change.get('path')
        if not check_package.safe_path(name) or name=='.' or str(Path(name))!=name or name in seen or hashlib.sha256(files.get(name,b'')).hexdigest()!=change.get('before_sha256'):
            raise ValueError('Proposed change is not bound to a contained current source file')
        seen.add(name)
        if not isinstance(change.get('replacement'),str) or len(change['replacement'].encode())>check_package.LIMIT:raise ValueError('Proposed changes need a bounded UTF-8 replacement')
    path=work/'proposals'/(policy.digest(value)+'.json');write_json(path,value)
    state=copy.deepcopy(state);state['proposed_fix']=dict(file=str(path),sha256=file_sha(path),summary=value.get('summary','Prepared source correction'))
    return core.event(state,'fix-proposed',dict(proposal=state['proposed_fix']),now())


def ensure_pack(state, work):
    if not state.get('snapshot'):
        return state
    state = copy.deepcopy(state)
    facts = copy.deepcopy(state['snapshot']['facts'])
    facts['hosts'] = state['answers'].get('hosts', {}).get('hosts', [])
    facts['host_cases'] = state['answers'].get('test-plan', {}).get('cases', [])
    facts['source_fingerprints'] = []
    expected = prepare_workflow.core.binding(facts)
    artifacts = state['artifacts']
    same_execution=bool(artifacts) and artifacts.get('binding')==expected
    if artifacts and artifacts.get('input_sha256')==policy.digest(facts):
        bundle = Path(artifacts['pack'])
        if work.resolve() not in bundle.resolve().parents:
            raise ValueError('Session pack must stay in its generated workspace')
        if prepare_workflow.check_bundle(bundle)['findings']:
            raise ValueError('Generated pack changed; use rebuild to retain it and generate a fresh pack')
        return state
    if artifacts and not same_execution:
        state = core.event(state, 'plan-binding-changed', {'previous_artifacts': artifacts,
            'previous_reports': state['host_rows']}, now())
        state['host_rows'] = {}
        for key in ('review-materials', 'desktop-install', 'requirement-review', 'upload',
                    'portal-validation', 'submit-review', 'review-decision', 'publish'):
            state['answers'].pop(key, None)
    bundle = work / ('pack-' + uuid.uuid4().hex[:12])
    input_path = work / ('input-' + uuid.uuid4().hex[:12] + '.json')
    write_json(input_path, facts)
    try:
        prepare_workflow.prepare(input_path, bundle, ['readiness', 'policy', 'obligations', 'postlaunch'])
    finally:
        input_path.unlink(missing_ok=True)
    plan = read_json(bundle / 'plan.json')
    if plan['binding'] != expected:
        raise ValueError('Generated plan binding differs from the inspected input')
    state['artifacts'] = dict(pack=str(bundle), plan=str(bundle / 'plan.json'), binding=plan['binding'],
                              input_sha256=policy.digest(facts),
                              archive=state['snapshot']['archive'], package_sha256=state['snapshot']['package_sha256'],
                              copy_fields=str(work / 'portal-copy-fields.json'), session_workspace=str(work))
    return state


def verify_saved_reports(state, work):
    """Cached pass flags cannot replace the source-bound evidence on resume."""
    document_records(state,work)
    review=state.get('jobs',{}).get('independent-review',{})
    if review.get('status')=='Completed':
        if review.get('binding')!=core.binding(state) or review.get('docs_sha256')!=state['docs']['content_sha256']:
            raise ValueError('Saved independent review belongs to different inputs')
        for name,sha in [('report','report_sha256'),('evidence','evidence_sha256')]:
            path=Path(review[name])
            if (work/'jobs').resolve() not in path.resolve().parents or path.is_symlink() or file_sha(path)!=review[sha]:
                raise ValueError('Saved independent review evidence changed')
    frozen_files = None
    for row in state['answers'].get('requirement-review', {}).get('decisions', []):
        evidence = row.get('evidence')
        row['evidence_state'] = 'Reference only; not verified'
        if not evidence:
            continue
        if evidence.get('binding') != core.binding(state):
            raise ValueError('Requirement evidence belongs to a different source or plan')
        if evidence.get('source_path'):
            if frozen_files is None:
                frozen_files = check_package.load_files(Path(state['snapshot']['archive']))
            data = frozen_files.get(evidence['source_path'])
            if data is None or hashlib.sha256(data).hexdigest() != evidence.get('sha256'):
                raise ValueError('Frozen source evidence digest mismatch')
            row['evidence_state'] = 'Frozen source digest checked'
        else:
            path = Path(evidence['file'])
            if (work/'requirement-evidence').resolve() not in path.resolve().parents or path.is_symlink() or file_sha(path) != evidence.get('sha256'):
                raise ValueError('Imported requirement evidence changed or escaped the session')
            row['evidence_state'] = 'Imported artifact integrity checked'
    if not state['host_rows']:
        return state
    plan = read_json(state['artifacts']['plan'])
    checked = {}
    for row in state['host_rows'].values():
        path = Path(row['report'])
        if (work / 'reports').resolve() not in path.resolve().parents or path.is_symlink():
            raise ValueError('Saved host evidence must remain inside the session reports directory')
        if file_sha(path) != row.get('report_sha256'):
            raise ValueError('Saved host report changed; re-import valid source-bound evidence')
        if str(path) not in checked:
            checked[str(path)] = host_reports.validate_report(read_json(path), path, plan)
    for key, row in state['host_rows'].items():
        match = next((r for r in checked[row['report']] if r['surface'] + ':' + r['id'] == key), None)
        if match is None or match['status'] != row['status'] or match['origin'] != row['origin'] or row['binding'] != plan['binding']:
            raise ValueError('Cached host status disagrees with its captured evidence')
    return state


def collect_requirement_evidence(state, value, input_path, work):
    """Copy explicitly supplied evidence; plain prose stays an unverified reference."""
    value = copy.deepcopy(value)
    frozen = None
    root = input_path.resolve().parent
    for row in value['decisions']:
        row['evidence_state'] = 'Reference only; not verified'
        evidence = row.get('evidence')
        if not evidence:
            continue
        if evidence.get('source_path'):
            if frozen is None: frozen = check_package.load_files(Path(state['snapshot']['archive']))
            data = frozen.get(evidence['source_path'])
            if data is None or hashlib.sha256(data).hexdigest() != evidence['sha256']:
                raise ValueError('Requirement source evidence does not match the frozen target')
            row['evidence_state'] = 'Frozen source digest checked'
        else:
            supplied = Path(evidence['file'])
            path = supplied if supplied.is_absolute() else root / supplied
            if path.is_symlink() or root not in path.resolve().parents or any(p.is_symlink() for p in [path,*path.parents] if p != root.parent):
                raise ValueError('Select a contained evidence file beside the response or in its subdirectories')
            if not path.is_file() or path.stat().st_size > 8 * 1024 * 1024 or file_sha(path) != evidence['sha256']:
                raise ValueError('Requirement evidence is missing, oversized or changed')
            target = work / 'requirement-evidence' / (evidence['sha256'] + '-' + path.name)
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            if target.is_symlink(): raise ValueError('Evidence destination must not be a symbolic link')
            shutil.copyfile(path, target)
            evidence['file'] = str(target)
            row['evidence_state'] = 'Imported artifact integrity checked'
        evidence['binding'] = core.binding(state)
    return value


def write_packet(state, work):
    if not state.get('snapshot'):
        return
    facts = state['snapshot']['facts']
    view = core.next_step(state)
    packet = dict(target=dict(name=state['snapshot']['name'], version=state['snapshot']['version'],
                              package_sha256=state['snapshot']['package_sha256']),
                  interface=facts['listing'], review_cases=facts['review_cases'],
                  demo_recording_url=state['snapshot'].get('demo_recording_url'),
                  creator_confirmations=state['answers'].get('creator-facts', {}),
                  understanding=state.get('understanding'),confirmed_choices=state.get('choices'),
                  proposed_interface=facts.get('listing_draft'),
                  documentation=state.get('docs'),independent_review=state.get('jobs',{}).get('independent-review'),
                  requirement_review=state['answers'].get('requirement-review', {}),
                  current_step=view['next']['id'], progress=view['progress'],
                  external_observations={k:v for k,v in state['answers'].items() if k in ('upload','portal-validation','submit-review','review-decision','publish')},
                  publication_state=dict(submitted=view['submitted'], published=view['published'],
                      provenance=view['external_status_provenance'], portal_actions_performed_by_tool=False),
                  credentials='Enter credentials only in the portal secure fields; none belong in this packet.',
                  artifacts=state['artifacts'], source_guides=[core.SUBMISSION, core.DESKTOP, core.TESTING],
                  simulation=state['synthetic'])
    write_json(work / 'portal-copy-fields.json', packet)
    write_json(work/'submission-bundle.json',dict(schema_version=2,source_origin=state.get('source_origin'),binding=core.binding(state),
        docs_sha256=state.get('docs',{}).get('content_sha256'),understanding_sha256=core.meaning(state.get('understanding')),
        choice_sha256=policy.digest(state.get('choices')),archive=state['snapshot']['archive'],
        generated_artifacts=state['artifacts'],pending_action=view['next']['id'],
        public_package_contains_working_evidence=False,portal_actions_performed=False))


def ingest(state, path, work):
    if not state['answers'].get('hosts') or not state['answers'].get('test-plan') or not state.get('artifacts'):
        raise ValueError('Fix the source-bound host plan before importing host evidence')
    report = read_json(path); plan = read_json(state['artifacts']['plan'])
    rows = host_reports.validate_report(report, path, plan)
    destination = work / 'reports' / file_sha(path); destination.mkdir(parents=True, exist_ok=True)
    for row in report['cases']:
        relative = Path(row['evidence']['file'])
        if relative.as_posix() == 'host-report.json':
            raise ValueError('Capture filename conflicts with the imported report filename')
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(path).resolve().parent / relative, target)
    write_json(destination / 'host-report.json', report)
    # Verify the copied evidence too. Paths and bytes stay source-bound after import.
    host_reports.validate_report(report, destination / 'host-report.json', plan)
    state = copy.deepcopy(state)
    for row in rows:
        state['host_rows'][row['surface'] + ':' + row['id']] = dict(status=row['status'], origin=row['origin'],
            observer=row['observer'], report=str(destination / 'host-report.json'), binding=plan['binding'],
            report_sha256=file_sha(destination / 'host-report.json'),
            verification='External observation claim; integrity checked, observer identity not authenticated')
    return core.event(state, 'host-report-ingested', dict(path=str(destination / 'host-report.json'),
                      host=report['host'], origin=report['origin'], cases=len(rows)), now())


def validate_imported_pack(path, state):
    checked = prepare_workflow.check_bundle(path)
    if checked['findings']:
        raise ValueError('The supplied audit pack failed integrity checks')
    facts = read_json(path / 'integration.json')
    snapshot = state.get('snapshot')
    if snapshot:
        if facts['source_revision'] != 'content-sha256:' + snapshot['content_sha256']:
            raise ValueError('The audit outputs belong to a different target')
        if facts.get('package_sha256') and facts['package_sha256'] != snapshot['package_sha256']:
            raise ValueError('The audit outputs identify a different archive')
    return core.event(state, 'audit-outputs-imported', dict(path=str(path), binding=checked['binding'],
                      source_match_verified=bool(snapshot)), now())


def export_session(state, work, output):
    if output.exists() or output.is_symlink():
        raise ValueError('Choose a new session-bundle filename')
    if work.resolve() == output.resolve() or work.resolve() in output.resolve().parents:
        raise ValueError('Export outside the session workspace')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('session.json', json.dumps(dict(state=state, workspace_root=str(work)), indent=2))
        if work.exists():
            for path in sorted(work.rglob('*')):
                if path.is_symlink(): raise ValueError('Session bundle must not contain symbolic links')
                if path.is_file(): archive.write(path, 'workspace/' + path.relative_to(work).as_posix())
    return str(output)


def restore_session(bundle, session, work):
    if session.exists() or work.exists():
        raise ValueError('Restore to a new session path and workspace')
    files = check_package.load_files(bundle)
    if 'session.json' not in files or any(n != 'session.json' and not n.startswith('workspace/') for n in files):
        raise ValueError('Not a wizard session bundle')
    payload = json.loads(files['session.json'], object_pairs_hook=check_package.no_duplicates)
    state = payload['state']
    state=core.migrate(state,now())
    old = payload['workspace_root'].replace('\\', '/').rstrip('/')
    def rebase(value):
        if isinstance(value, dict): return {k: rebase(v) for k, v in value.items()}
        if isinstance(value, list): return [rebase(v) for v in value]
        if isinstance(value, str):
            normalized = value.replace('\\', '/')
            if normalized == old: return str(work)
            if normalized.startswith(old + '/'):
                return str(work.joinpath(*normalized[len(old)+1:].split('/')))
        return value
    state = rebase(state)
    if state.get('snapshot'):
        archived = Path(state['snapshot']['archive'])
        sha = state['snapshot']['package_sha256']
        if not isinstance(sha, str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            raise ValueError('Invalid frozen target digest')
        if archived.parent.resolve() != (work/'archives').resolve() or archived.name != sha+'.zip':
            raise ValueError('Frozen target must be contained in the restored archives directory')
    work.mkdir(parents=True, mode=0o700)
    for name, data in files.items():
        if name == 'session.json': continue
        destination = work.joinpath(*Path(name).parts[1:])
        destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(data)
    if state.get('snapshot'):
        if file_sha(state['snapshot']['archive']) != state['snapshot']['package_sha256']:
            raise ValueError('Restored target digest mismatch')
        state['source_path'] = state['snapshot']['archive']
    state['notice'] = 'Restored the saved session and exact frozen target. Attach updated source when making changes.'
    return core.event(state, 'session-restored', {'bundle': str(bundle)}, now())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('start','next','attach','answer','choose','ingest','pause','resume','defer','revisit','rebuild','export','restore',
                 'sync-docs','search-docs','refine','review','run-review','propose-fix','apply-fix','jobs'):
        p = sub.add_parser(name); p.add_argument('--session', type=Path, required=True)
        p.add_argument('--expected-revision', type=int)
        if name == 'start':
            p.add_argument('--source'); p.add_argument('--pack', type=Path)
            p.add_argument('--goal', choices=('audit','private-preparation','public-submission'))
            p.add_argument('--host', choices=('chatgpt', 'codex'), action='append')
            p.add_argument('--synthetic', action='store_true')
            p.add_argument('--actor-id',default='host-primary');p.add_argument('--docs-mode',choices=('live','offline'))
            p.add_argument('--docs-input',type=Path)
        if name in ('start','attach'):
            p.add_argument('--ref');p.add_argument('--plugin-root')
            p.add_argument('--source-info',type=Path)
        if name == 'attach': p.add_argument('--source',required=True)
        if name == 'answer':
            p.add_argument('--step', required=True); p.add_argument('--input', type=Path, required=True)
        if name == 'ingest': p.add_argument('--report', type=Path, required=True)
        if name == 'defer': p.add_argument('--reason', required=True)
        if name == 'revisit': p.add_argument('--step', required=True)
        if name == 'export': p.add_argument('--output', type=Path, required=True)
        if name == 'restore': p.add_argument('--bundle', type=Path, required=True)
        if name in ('choose','refine','review','apply-fix','propose-fix'):p.add_argument('--input',type=Path,required=True)
        if name=='sync-docs':
            p.add_argument('--input',type=Path);p.add_argument('--mode',choices=('live','offline'))
        if name=='search-docs':p.add_argument('--query',required=True)
        if name=='run-review':p.add_argument('--runner',type=Path,required=True)
    args = parser.parse_args(argv)
    try:
        session = args.session.absolute()
        if session.is_symlink(): raise ValueError('Session must not use a symbolic link')
        work = session.with_name(session.stem + '.files')
        if work.is_symlink(): raise ValueError('Session workspace must not use a symbolic link')
        source = getattr(args, 'source', None)
        if source and not str(source).startswith('https://'):
            outside(session, source); outside(work, source)
        with session_lock(session):
            if args.command == 'restore':
                state = restore_session(args.bundle, session, work)
            elif args.command == 'start':
                if session.exists(): raise ValueError('Session exists; use next to resume it')
                state = core.new_session(uuid.uuid4().hex, now(), args.synthetic, args.goal, args.host)
                state['actor_id']=args.actor_id
                if args.docs_mode:state['docs_mode']=args.docs_mode
            else:
                state = core.migrate(read_json(session),now())
            if args.expected_revision is not None and state['revision'] != args.expected_revision:
                raise ValueError('Session changed; read next and use its current revision')
            if args.command == 'export':
                outside(args.output, state.get('source_path'))
                if args.output.exists() or args.output.is_symlink() or args.output.absolute() == session or work.resolve() in args.output.resolve().parents:
                    raise ValueError('Export to a new file outside the session and target workspace')
            work.mkdir(parents=True, exist_ok=True, mode=0o700)
            if args.command in ('start','attach') and source:
                acquired=acquire_source(source,work,args.ref,args.plugin_root)
                state['source_origin']=acquired['origin']
                if args.source_info:
                    provenance=read_json(args.source_info)
                    if set(provenance)-{'archive_sha256','provider','commit','locator','visibility','ref','plugin_root','observed_at'}:
                        raise ValueError('Source provenance accepts only repository metadata, never credentials')
                    if provenance.get('archive_sha256')!=file_sha(acquired['path']) or not provenance.get('provider') or not re.fullmatch('[0-9a-f]{40}',provenance.get('commit','')):
                        raise ValueError('Connector source provenance needs the exact archive hash, provider and pinned commit')
                    url=urlsplit(provenance.get('locator',''))
                    if url.scheme!='https' or url.netloc!='github.com' or url.query or url.fragment:raise ValueError('Connector provenance must identify a GitHub repository')
                    state['source_origin']=dict(provenance,kind='github',external_observation=True)
                state['source_pending']=acquired if acquired['roots'] else None
                state['source_path']=None if acquired['roots'] else acquired['path']
            state = observe(state, session, work)
            supplied_docs=read_json(args.docs_input) if args.command=='start' and args.docs_input else None
            if args.command=='sync-docs':
                if args.mode:state['docs_mode']=args.mode
                supplied_docs=read_json(args.input) if args.input else None
            state=prepare_state(state,session,work,refresh_docs=args.command=='sync-docs',supplied_docs=supplied_docs)
            if args.command == 'start' and args.pack:
                state = validate_imported_pack(args.pack, state)
                state['imported_pack'] = str(args.pack.resolve())
            if args.command == 'attach' and state.get('imported_pack'):
                validate_imported_pack(Path(state['imported_pack']), state)
                state.pop('imported_pack', None)
            if args.command == 'answer':
                value = read_json(args.input)
                if args.step == 'requirement-review':
                    if core.next_step(state)['next']['id'] != args.step:
                        raise ValueError('Requirement evidence is accepted at its current preparation step')
                    core.validate_answer(state, args.step, value)
                    value = collect_requirement_evidence(state, value, args.input, work)
                state = core.answer(state, args.step, value, now())
                state = observe(state, session, work)
            elif args.command=='choose':
                state=core.apply_choices(state,read_json(args.input),now())
                if state.pop('apply_proposal',False):
                    proposal=state.pop('proposed_fix');path=Path(proposal['file'])
                    if (work/'proposals').resolve() not in path.resolve().parents or path.is_symlink() or file_sha(path)!=proposal['sha256']:
                        raise ValueError('Prepared fix changed or escaped the proposal directory')
                    state=apply_fix(state,read_json(path),work);state=observe(state,session,work)
                if 'selected_root' in state:
                    pending=state['source_pending'];root=state.pop('selected_root')
                    acquired=acquire_source(pending['path'],work,plugin_root=root)
                    state['source_origin']=dict(pending['origin'],plugin_root=root)
                    state['source_path']=acquired['path'];state['source_pending']=None
                    state=observe(state,session,work)
                state=observe(state,session,work)
            elif args.command=='refine':state=refine_understanding(state,read_json(args.input))
            elif args.command=='review':state=import_review(state,read_json(args.input),args.input,work)
            elif args.command=='run-review':
                runner=read_json(args.runner)
                if not isinstance(runner,list) or not runner or not all(isinstance(v,str) for v in runner):raise ValueError('Runner is an explicit argv array; no shell command')
                job=state['jobs'].get('independent-review')
                if not job:raise ValueError('Confirm the source-derived setup before dispatching review')
                request=read_json(job['request']);request['request_sha256']=job['request_sha256']
                folder=work/'jobs'/('run-'+uuid.uuid4().hex);folder.mkdir(parents=True)
                try:
                    run=subprocess.run(runner,input=json.dumps(request),text=True,capture_output=True,timeout=120,shell=False)
                    (folder/'stdout.txt').write_text(run.stdout);(folder/'stderr.txt').write_text(run.stderr)
                    if run.returncode:raise ValueError('Review runner returned exit '+str(run.returncode))
                    report=json.loads(run.stdout)
                    report.update(binding=core.binding(state),docs_sha256=state['docs']['content_sha256'],request_sha256=job['request_sha256'],
                        provider=report.get('provider','configured-agent-runner'),reviewer_id=report.get('reviewer_id','runner:'+uuid.uuid4().hex),
                        evidence=dict(file='stdout.txt',sha256=file_sha(folder/'stdout.txt')))
                    write_json(folder/'report.json',report);state=import_review(state,report,folder/'report.json',work)
                except (subprocess.TimeoutExpired,ValueError) as exc:
                    state['jobs']['independent-review'].update(status='Unavailable',reason=str(exc),logs=str(folder))
                    state=core.event(state,'review-runner-unavailable',{'reason':str(exc)},now())
            elif args.command=='apply-fix':
                state=apply_fix(state,read_json(args.input),work);state=observe(state,session,work)
            elif args.command=='propose-fix':state=propose_fix(state,read_json(args.input),work)
            elif args.command == 'pause':
                state['paused'] = True; state = core.event(state, 'paused', {}, now())
            elif args.command == 'resume':
                state['paused'] = False; state = core.event(state, 'resumed', {}, now())
            elif args.command == 'defer': state = core.defer(state, args.reason, now())
            elif args.command == 'revisit':
                state = core.revisit(state, args.step, now()); state = observe(state, session, work)
            elif args.command == 'rebuild':
                state = core.event(state, 'artifacts-rebuild-requested', {'previous_artifacts': state['artifacts']}, now())
                state['artifacts'] = {}
            state=prepare_state(state,session,work)
            if core.next_step(state)['next']['id']=='upload' and state['docs'].get('release_bound_to')!=policy.digest(core.binding(state)):
                state=prepare_state(state,session,work,refresh_docs=True)
                state['docs']['release_bound_to']=policy.digest(core.binding(state))
            state = ensure_pack(state, work)
            if args.command == 'ingest': state = ingest(state, args.report, work)
            state = verify_saved_reports(state, work)
            write_packet(state, work)
            result = core.next_step(state)
            state['question_plan']=core.question_plan(state)
            result.update(question_plan=state['question_plan'],native_widget=state['question_plan']['payload'] if state['question_plan'] else None,
                pending_jobs=[dict(kind=kind,**job) for kind,job in state['jobs'].items() if job.get('status') in ('Pending','Running')],
                current_policy_retrieved=bool(state.get('docs',{}).get('selected_ids')) and all(d['status']=='current' for d in state['docs']['documents'] if d['role']=='primary'),
                documentation_gaps=state.get('docs',{}).get('gaps',[]),
                independent_review_verified=state['jobs'].get('independent-review',{}).get('status')=='Completed' and state['jobs']['independent-review'].get('origin')=='observed')
            if args.command=='search-docs':result['search_results']=policy.search_documents(document_records(state,work),args.query)
            result['session_path'] = str(session)
            if args.command == 'export':
                if args.output.absolute() == session:
                    raise ValueError('Export must not replace the session')
                result['session_bundle'] = export_session(state, work, args.output)
            write_json(session, state)
            print(json.dumps(result, indent=2))
            return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'Input rejected; session was not advanced', 'message': str(exc)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
