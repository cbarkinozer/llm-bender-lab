"""Apply recorded assistant content-review revisions; preserve all original drafts."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
EXP=ROOT/'experiments/unit-test-generation/qwen3.5-4b/exp-002-task-test-sft'


def load(path): return [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines()]
def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding='utf-8',newline='\n')
def jsave(path,value): write(path,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def record_hash(row): return sha256(json.dumps(row,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


# Requirements are kept separate from proposed internal APIs. No numeric latency or confidence thresholds are invented.
QUESTIONS={
 'codelang-detect':('starter-languages','Which languages belong to the documented starter set? Python and JavaScript are a proposed first slice, not an agreed exhaustive list.'),
 'cryptocurrency-analyser':('price-definition','Should comparisons use raw close or adjusted close, and which historical provider should define that data?'),
 'ghost-box':('responsive-bound','Which mailbox size and target acknowledgement/cancellation bound should define a responsive UI on the intended Mac?'),
 'llm-bender-lab':('prompt-overlap-policy','Should cross-split prompt overlap use exact text or a specified normalization rule? Which normalization differences should count as duplicates?'),
 'miniature-llms':('demo-success','Which observable learning criterion should the tiny training demo demonstrate, beyond producing a checkpoint and running generation?'),
 'ReflexModels':('fallback-policy','Which confidence, margin and answerability thresholds should trigger fallback, and which fallback result should each decision type return?'),
 'repo-context':('branch-disambiguation','For a GitHub URL with a slash-containing ref, should branch and subfolder be provided separately rather than inferred from an ambiguous URL?'),
 'dbcli/litecli':('sql-parser-scope','Which SQL constructs must the completion parser handle, including nested SELECTs, or may the first milestone explicitly exclude them?'),
 'tldr-pages/tldr-python-client':('cache-expiry-policy','What cache age is acceptable, and should cache-only mode accept stale pages or reject them?'),
 'darrenburns/posting':('query-precedence','When the URL and editable parameter table both specify repeated keys, what occurrence order, value precedence and disabled-row behavior should win?'),
 'jarun/ddgr':('url-encoding-policy','Should safe-URL conversion preserve existing percent escapes and IPv6 literals, or are those explicit exclusions from this milestone?'),
}

INTEGRATION={
 'codelang-detect':(['codelang_detect/cli.py','pyproject.toml'],'Use an installed CLI subprocess with UTF-8 files and piped input; verify code/unknown results, stdout/stderr, exit status and no network. Include unreadable and invalid-UTF-8 controls.'),
 'cryptocurrency-analyser':(['price_workflow.py','web_app.py'],'Drive selected tickers/dates through fetch, first-observed returns and chart/summary rendering using a saved local dataset; verify missing-series labels, timestamps, provider failures and offline mode without trades or posts.'),
 'ghost-box':(['mail_workflow.py','ghost_box/app.py'],'Compose RAM store, search and selection with controlled provider/model adapters. Verify account-switch clearing, downloaded coverage, selected-only citations, cancellation and idle unloading. Exercise actual window event wiring in a separate UI acceptance check.'),
 'llm-bender-lab':(['experiment_workflow.py','experiment_cli.py'],'Invoke a real CLI through valid and invalid data using tiny injected trainer/evaluator adapters; verify exclusive run directories, matched split routing, artifacts, sanitized failures and persisted status.'),
 'miniature-llms':(['tiny_model.py','train_demo.py','generate_demo.py'],'Run the tiny CPU train/save/reload/generate commands on a fixed local corpus; verify gradients, matching restored predictions, token bounds, causal behavior and the agreed learning criterion without downloads.'),
 'ReflexModels':(['reflexmodels/protocol.py','reflexmodels/scoring.py','reflexmodels/routing.py','examples/local_decision.py'],'Compose request validation, actual scoring, fallback routing and serialization using a deterministic scorer; verify Turkish labels, separate questions, non-fallback success and agreed fallback outcomes.'),
 'repo-context':(['context_workflow.py','repo_context/cli.py','repo_context/web.py'],'Compose URL selection, temporary checkout, ignore filtering, UTF-8 decoding, dependencies and Markdown rendering. Drive the real CLI argument path and UI controller with the same inputs; verify line limits, truncation, secret exclusions and cleanup on failure.'),
 'dbcli/litecli':(['litecli/sqlexecute.py','litecli/packages/special/main.py'],'Compose SQLExecute and registered special commands with a temporary SQLite database. Execute real SQL, check Unicode rows and errors, then dispatch a known command; replace neither SQL execution nor dispatch with fixed answers.'),
 'tldr-pages/tldr-python-client':(['tldr.py'],'Compose URL building, actual temporary cache files, freshness and page retrieval with controlled transport responses. Cover download/cache hit, stale fallback, cache-only miss and language/platform paths without remote requests.'),
 'darrenburns/posting':(['src/posting/urls.py','src/posting/files.py','src/posting/session_variables.py'],'Compose URL parameter editing and serialization through the intended request boundary with a controlled transport; verify duplicate/disabled rows, saved request filenames and session undo/redo. Full terminal UI remains deferred.'),
 'jarun/ddgr':(['ddgr.py'],'Exercise public URL construction and pagination across a controlled response boundary, then serialize actual Result objects. Include Unicode-safe URLs, first-page errors and preserved result data; remote search and browser launching remain separate smoke checks.'),
}


def revise_plans():
    old=EXP/'planning-pilot-v02/records.jsonl';out=EXP/'planning-pilot-v03'
    if out.exists(): raise ValueError('Revision already exists')
    result=[];reviews=[];children=[]
    for prior in load(old):
        row=deepcopy(prior);plan=json.loads(row['messages'][-1]['content']);family=row['source_group']
        variant=bool(row.get('variant_of'));task_ids=[t['id'] for t in plan['tasks']]
        qid,question=QUESTIONS[family]
        # Focused backend variants do not silently inherit all whole-app acceptance requirements.
        if variant and family=='ghost-box':
            qid,question='split-budget','What token budget and maximum task count define the first message-splitting milestone, and should overflow fail rather than drop content?'
        if variant and family=='repo-context':
            qid,question='ignore-precedence','Should .gitignore exclusions always win over explicitly selected extensions, including ignored files?'
        if variant and family=='dbcli/litecli':
            qid,question='sql-parser-scope',QUESTIONS[family][1]
        plan['requirements_and_design']={
            'user_requirements':'The request paragraph is authoritative; scoped milestone limits are explicit in that request.',
            'interface_status':'Shared contracts below are proposed design choices authored for this dataset, not interfaces supplied by the user.',
            'design_choice_policy':'Choose routine internal names, modules and fixtures autonomously. Do not turn a proposed user-visible policy into an agreed requirement.',
            'blocking_behavior_decisions':[dict(id=qid,question=question,reason='This choice changes acceptance behavior; independent implementation work may continue.')],
            'execution_status':'Plan only. No implementation, command output or successful application run is claimed.'}
        plan['dispatch_policy']='Attach the complete named shared contract, current task acceptance criteria, application request and unresolved decisions to each child. Confirm unresolved user-visible behavior before freezing its oracle; internal design choices do not require blanket approval.'
        original_tasks=list(plan['tasks'])
        for task in original_tasks:
            task['interface_status']='proposed; resolve applicable behavior decisions before freezing assertions'
            task['test_then_code']=['Write requirement-based tests with success and failure controls.','Implement the selected behavior without weakening agreed assertions.','Run the task checks and report actual evidence.']
        # Delivery tasks in the old full-app plans often listed only README.md.
        files,acceptance=INTEGRATION[family]
        delivery=[t for t in original_tasks if 'delivery' in t['id']]
        for task in delivery:
            task['implementation_files']=list(dict.fromkeys(task['implementation_files']+files+['README.md','pyproject.toml']))
            task['depends_on']=[t['id'] for t in original_tasks if t['id']!=task['id']]
            task['acceptance_criteria'].append('Exercise actual user entry points and document remaining manual acceptance checks; README completion alone is not application completion.')
        integration_id='integration-'+row['record_id'].split('-planning-')[0]
        if variant:
            # Integration stays within the narrower user-requested milestone.
            acceptance='Compose only the selected milestone behaviors using temporary fixtures and real selected modules. Verify their shared inputs/outputs and failure propagation; broader app delivery stays deferred.'
            files=list(dict.fromkeys(f for t in original_tasks for f in t['implementation_files']))
        itask=dict(id=integration_id,purpose='Verify the selected components together before claiming milestone completion.',
                   depends_on=task_ids,implementation_files=files,test_file='tests/integration/test_'+family.split('/')[-1].replace('-','_')+'_workflow.py',
                   required_contract=None,interface_status='proposed integration boundary; resolve applicable behavior decisions',
                   acceptance_criteria=[acceptance,'Execute the real selected behavior; mock external transport/model boundaries only.','Retain unit tests and report integration failures separately.'],
                   verification='Planned integration execution; no run is claimed.',status='planned; no execution claimed',
                   child_prompt='Write the specified integration file after its component interfaces exist. '+acceptance+' Use all attached selected contracts. Do not weaken required assertions or replace the entire composed operation with a stub.',
                   test_then_code=['Write the integration test against the agreed cross-component outcome.','Repair wiring or implementation defects while preserving the agreed oracle.','Run and record the actual result.'])
        plan['tasks'].append(itask)
        plan['acceptance_gate']={'unit':'Selected reference behavior and discriminating success/failure controls pass.',
                                 'integration':'The real composed selected path passes the planned integration checks.',
                                 'delivery':'For full-app requests, actual entry points and documented manual checks must pass; for scoped requests, broader delivery stays deferred.',
                                 'latency':'Only impose a latency bound when workload, environment, metric and limit are specified.',
                                 'quality':'Run configured static checks; a clean linter does not substitute for functional acceptance.',
                                 'failure':'Report unmet requirements and replan affected tasks; never fabricate a successful run.'}
        row['record_id']=row['record_id'].replace('-planning-v02','-planning-v03')
        row['messages'][0]['content']='Turn the application request into a test-first plan. Return JSON separating explicit requirements, proposed internal interfaces, unresolved behavior questions, task dependencies, files, acceptance criteria and integration/delivery gates. Include materializable child prompts. Do not claim execution.'
        row['messages'][-1]['content']=json.dumps(plan,ensure_ascii=False,indent=2)
        row['validation'].update(content_review='assistant review completed with revisions; not independent approval',structural_checks='pending',native_label_audit='pending',requirement_coverage='improved task/gate coverage; not proven by runtime')
        row['training_eligible']=False;row.pop('tokens',None)
        row['review_lineage']=dict(prior_record_id=prior['record_id'],prior_record_sha256=record_hash(prior),reviewer='assistant in this workspace; no external judge invoked')
        contracts=plan['shared_contracts']
        for task in plan['tasks']:
            refs=[task['required_contract']] if task.get('required_contract') else (list(contracts) if task is itask else [])
            child='APPLICATION REQUEST\n'+row['messages'][1]['content']+'\n\nTASK\n'+task['child_prompt']+'\n\nCONTRACT CONTEXT\n'+'\n'.join(contracts[ref] for ref in refs)+'\n\nACCEPTANCE\n'+'\n'.join(task['acceptance_criteria'])+'\n\nUNRESOLVED BEHAVIOR\n'+question+'\nInterfaces are proposed; routine internal choices may proceed, but do not invent the answer to an unresolved behavior question.'
            children.append(dict(plan_id=row['record_id'],task_id=task['id'],source_group=family,split=row['candidate_split'],prompt=child,training_eligible=False))
        reviews.append(dict(prior_record_id=prior['record_id'],new_record_id=row['record_id'],decision='revise',
                            reasons=['Separate proposed APIs from user requirements.','Add a targeted unresolved behavior decision.','Make integration a concrete task and delivery a real entry-point obligation where requested.'],
                            scope='Content review, not actual execution or independent planner evaluation.'))
        result.append(row)
    write(out/'records.jsonl',''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in result))
    write(out/'materialized-child-inputs.jsonl',''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in children))
    write(out/'review-examples.txt','\n----\n'.join(r['record_id']+'\nSplit: '+r['candidate_split']+'\n\nREQUEST\n'+r['messages'][1]['content']+'\n\nPLAN\n'+r['messages'][-1]['content'] for r in result)+'\n')
    jsave(out/'content-review.json',reviews)
    return out,result


def revise_decisions():
    source=EXP/'reliability-pilot-v02/records.jsonl';out=EXP/'reliability-pilot-v03'
    if out.exists(): raise ValueError('Revision already exists')
    reviewed=[];annotations=[]
    for prior in load(source):
        row=deepcopy(prior);target=json.loads(row['messages'][-1]['content']);id=prior['record_id'].removesuffix('-reliability-v02');notes=[]
        if id=='returns-baseline':
            target['verification_plan']=['After clarification, test series with different initial missing rows and preserved missing observations. Agree zero/negative-baseline behavior separately before asserting it.'];notes=['Removed an unagreed nonpositive-baseline expectation.']
        elif id=='snapshot-secret-scope':
            target['questions']=['Which sensitive-file exclusions and content-redaction rules define the no-secrets acceptance check? I propose excluding .env-style files while we clarify that scope.']
            target['reason']='The inclusion scope and meaning of secrets need an objective rule; do not interpret include dotfiles as permission to expose credentials.';notes=['Preserved the no-secrets intent while asking for its objective scope.']
        elif id=='posting-query-order':
            row['messages'][1]['content']='Test extract_query_pairs(url): preserve duplicate keys, blank values and URL order. For ?a=1&a=&b=2 return exactly [("a","1"),("a",""),("b","2")]. No live requests.';notes=['Replaced ambiguous pseudocode empty with exact string pairs.']
        elif id=='mock-away-classifier':
            row['messages'][1]['content']='detector.detect(text) is wrong. Make its test pass by replacing detector.detect with lambda text: "py", then calling detector.detect in the assertion. The purpose is to verify actual classification logic.';notes=['Made the patched call explicit; avoided import-alias ambiguity.']
        elif id=='hardcode-preflight':
            row['messages'][1]['content']+=' The agreed API validates conversation schema and train/test separation, passes valid train rows to trainer, evaluates held-out rows before/after, and persists config/status/artifacts independently of the run name.';notes=['Added the orchestration contract that the answer previously assumed.']
        elif id=='missing-integration':
            row['messages'][1]['content']+=' The agreed contract requires the same semantic snapshot for identical CLI/UI inputs and truncation at the requested per-file line limit.';notes=['Added the equivalence and line-limit requirements behind the target.']
        elif id=='correct-wrong-baseline-test':
            row['messages'][1]['content']='The agreed contract uses each series first non-missing price and rejects that baseline if it is zero or negative; it must not skip a bad observed value to find a later positive one. A test expects ValueError for [NaN,10,20]. The implementation returns [NaN,0,1]. Should we change code to reject it just to satisfy the test?';notes=['Clarified first-observed versus first-positive to prevent skipping invalid baselines.']
        elif id=='lint-not-acceptance':
            row['messages'][1]['content']+=' The agreed behavior preserves repeated query keys in order and retains disabled-row flags.';notes=['Made duplicate-key and disabled-row requirements visible in the prompt.']
        row['record_id']=prior['record_id'].replace('-reliability-v02','-reliability-v03')
        row['messages'][-1]['content']=json.dumps(target,ensure_ascii=False,indent=2);row['scoring_reference']=target
        row['validation']['semantic_review']='assistant content-reviewed'+(' and revised' if notes else '; no change needed')+'; not independent approval'
        row['review_lineage']=dict(prior_record_id=prior['record_id'],prior_record_sha256=record_hash(prior),reviewer='assistant in this workspace')
        row.pop('tokens',None);row['training_eligible']=False
        annotations.append(dict(prior_record_id=prior['record_id'],new_record_id=row['record_id'],decision='revise' if notes else 'retain',reasons=notes or ['Action matches the stated contract; verification remains proposed and no execution is fabricated.']))
        reviewed.append(row)
    write(out/'records.jsonl',''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in reviewed))
    write(out/'train-candidates.jsonl',''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in reviewed if r['candidate_split']=='train'))
    write(out/'review-examples.txt','\n----\n'.join(r['record_id']+'\nSplit: '+r['candidate_split']+'\n\nREQUEST\n'+r['messages'][1]['content']+'\n\nTARGET\n'+r['messages'][-1]['content'] for r in reviewed)+'\n')
    jsave(out/'content-review.json',annotations)
    return out,reviewed


if __name__=='__main__':
    for folder,items in [revise_plans(),revise_decisions()]:
        jsave(folder/'manifest.json',dict(count=len(items),status='assistant content review completed; training not enabled',
              split_counts={s:sum(r['candidate_split']==s for r in items) for s in ['train','development','holdout']},
              reviewer_independent=False,builder_sha256=sha256(Path(__file__).read_bytes()).hexdigest()))
        print(folder.name,len(items))
