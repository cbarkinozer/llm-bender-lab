"""Descriptive dataset profile and near-duplicate candidate retrieval; no model runs."""
import argparse
import ast
from collections import Counter,defaultdict
import csv
from hashlib import sha256
import importlib.metadata
import itertools
import json
import math
from pathlib import Path
import re
import statistics
import sys

from active_tdd_data import EXP,ROOT,active_paths,rows,read_json,inside
from native_tdd_labels import encode_conversation

# Explicit analyst taxonomy, not model-inferred ground truth or a quality score.
DOMAINS={
 'codelang-detect':('Developer tooling','Code-language detection'),
 'cryptocurrency-analyser':('Finance','Cryptocurrency time series'),
 'ghost-box':('Productivity','Local email assistant'),
 'ReflexModels':('AI/ML tooling','Structured decisions and calibration'),
 'llm-bender-lab':('AI/ML tooling','Experiment orchestration'),
 'miniature-llms':('AI/ML tooling','Neural-network components'),
 'repo-context':('Developer tooling','Repository context extraction'),
 'dbcli/litecli':('Databases','SQLite terminal client'),
 'tldr-pages/tldr-python-client':('Developer tooling','Offline documentation client'),
 'darrenburns/posting':('Network clients','HTTP request client'),
 'jarun/ddgr':('Network clients','Terminal web search')}

BEHAVIORS={
 'classification':['language-basic','language-rules','litecli-sql-destructive-detection'],
 'input-output-adapter':['language-cli-success','prices-fetch'],
 'validation-and-errors':['language-cli-errors','mail-quote-validation','decision-requests','experiment-preflight'],
 'numeric-transformation':['prices-returns','prices-charts','decision-probabilities','decision-calibration','decision-ordinal'],
 'workflow-composition':['prices-analysis','mail-fetch-coverage','mail-selected-inference','experiment-matched-evaluation','experiment-failure-reporting','snapshot-safe-context','litecli-sqlite-query-execution','tldr-python-client-cache-network-routing'],
 'state-and-lifecycle':['mail-store','mail-cancellation','mail-model-lifecycle','decision-shared-state','tldr-python-client-cache-freshness','posting-session-undo-redo','posting-session-history-limit','ddgr-search-pagination'],
 'text-search-transform':['mail-search','mail-splitting','snapshot-text-decoding','litecli-completion-last-word'],
 'routing-and-selection':['decision-fallback','snapshot-controller-routing','litecli-special-command-dispatch','tldr-python-client-platform-priority'],
 'filesystem-and-artifacts':['experiment-artifact-isolation','snapshot-file-tree','litecli-path-completion','tldr-python-client-cache-path-selection','posting-request-filenames'],
 'numeric-model-behavior':['tensor-rms-normalization','tensor-rotary-positions','tensor-model-composition','tensor-causal-independence','tensor-training-generation'],
 'parsing-and-serialization':['tensor-checkpoint-roundtrip','snapshot-dependencies','snapshot-url-routing','litecli-sql-table-identifiers','tldr-python-client-language-selection','tldr-python-client-page-url','posting-path-parameters','posting-query-pair-merge','ddgr-unicode-safe-urls','ddgr-result-serialization']}
BEHAVIOR_BY_TASK={task:kind for kind,tasks in BEHAVIORS.items() for task in tasks}


def save(path,text):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8',newline='\n')
def jsave(path,value):save(path,json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def digest(path):return sha256(path.read_bytes()).hexdigest()


def stats(values):
    values=sorted(values)
    if not values:return dict(n=0)
    def percentile(p):
        at=(len(values)-1)*p;low=math.floor(at);high=math.ceil(at)
        return values[low]+(values[high]-values[low])*(at-low)
    mean=statistics.mean(values)
    return dict(n=len(values),total=sum(values),mean=mean,std_population=statistics.pstdev(values),
                std_sample=statistics.stdev(values) if len(values)>1 else None,
                min=values[0],p10=percentile(.1),median=percentile(.5),p90=percentile(.9),p95=percentile(.95),max=values[-1],
                coefficient_of_variation=statistics.pstdev(values)/mean if mean else None)


def diversity(counts):
    n=sum(counts.values());prob=[v/n for v in counts.values()] if n else []
    entropy=-sum(p*math.log(p) for p in prob)
    return dict(counts=dict(counts),categories=len(counts),entropy_nats=entropy,effective_categories=math.exp(entropy) if n else 0,
                largest_share=max(prob,default=0),note='Descriptive balance only; not independent-task count or generalization quality.')


def complexity(source):
    from radon.complexity import cc_visit,cc_rank
    from radon.raw import analyze
    from radon.visitors import Function,Class
    def functions(blocks):
        output=[];seen=set()
        def visit(block):
            if isinstance(block,Function):
                key=(block.name,block.lineno,block.col_offset)
                if key in seen:return
                seen.add(key);output.append(block)
                for closure in block.closures:visit(closure)
            elif isinstance(block,Class):
                for method in block.methods:visit(method)
                for inner in block.inner_classes:visit(inner)
        for block in blocks:visit(block)
        return output
    defaults=functions(cc_visit(source));without=functions(cc_visit(source,no_assert=True));table={(f.name,f.lineno):f for f in without}
    result=[]
    for block in defaults:
        alternate=table[(block.name,block.lineno)]
        result.append(dict(name=block.name,line=block.lineno,kind='test' if block.name.startswith('test_') else 'helper',
                           cc=block.complexity,cc_rank=cc_rank(block.complexity),cc_without_asserts=alternate.complexity))
    raw=analyze(source);tree=ast.parse(source)
    imports=sorted({(n.module or '').split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}|
                   {a.name.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names})
    tests=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_')]
    shapes=[]
    for test in tests:
        normalized=ast.dump(test,include_attributes=False)
        # Ignore only test function's own name for exact body reuse checks.
        normalized=normalized.replace("name='"+test.name+"'","name='TEST'",1)
        shapes.append(dict(name=test.name,sha256=sha256(normalized.encode()).hexdigest()))
    return dict(sloc=raw.sloc,lloc=raw.lloc,physical_lines=raw.loc,functions=result,test_functions=len(tests),
                assertions=sum(isinstance(n,ast.Assert) for n in ast.walk(tree)),
                assertion_helper_calls=sum(isinstance(n,ast.Call) and ast.unparse(n.func).rsplit('.',1)[-1].startswith('assert_') for n in ast.walk(tree)),
                imports=[x for x in imports if x],test_body_hashes=shapes,
                exact_ast_sha256=sha256(ast.dump(tree,include_attributes=False).encode()).hexdigest())


def purpose(row,track):
    if track=='tests':
        if row.get('acceptance_criteria'):
            return row['task_id'].replace('-',' ')+' '+ ' '.join(row['acceptance_criteria'])
        text=row['messages'][1]['content']
        return row['task_id'].replace('-',' ')+' '+text.split('INTERFACE AND ACCEPTANCE CONTRACT\n',1)[1].split('\n\nCONTEXT',1)[0]
    if track=='planning':
        plan=json.loads(row['messages'][-1]['content'])
        return row['messages'][1]['content']+' '+' '.join(t['purpose']+' '+' '.join(t['acceptance_criteria']) for t in plan['tasks'] if not t['id'].startswith('integration-'))
    target=json.loads(row['messages'][-1]['content'])
    return row['messages'][1]['content']+' '+target['action']+' '+target.get('reason',target.get('diagnosis',''))


STOP=set('a an the and or of to in on for from with is are be as by this that these those it its at into only should must before after then use using test tests task tasks file files write pytest python contract agreed expected actual'.split())


def terms(text):
    words=[w for w in re.findall(r'\w+',text.casefold().replace('_',' ')) if len(w)>1 and w not in STOP]
    return Counter(words+[' '.join(pair) for pair in zip(words,words[1:])])


def similarities(texts):
    counts=[terms(text) for text in texts];frequency=Counter(term for doc in counts for term in doc);n=len(counts)
    vectors=[]
    for doc in counts:
        vector={term:(1+math.log(count))* (math.log((1+n)/(1+frequency[term]))+1) for term,count in doc.items()}
        norm=math.sqrt(sum(v*v for v in vector.values()));vectors.append({k:v/norm for k,v in vector.items()} if norm else {})
    pairs=[]
    for i,j in itertools.combinations(range(n),2):
        small,large=(vectors[i],vectors[j]) if len(vectors[i])<=len(vectors[j]) else (vectors[j],vectors[i])
        score=sum(v*large.get(k,0) for k,v in small.items())
        pairs.append((score,i,j))
    return sorted(pairs,reverse=True)


def references(test_rows):
    """Optional audit-only code metrics; never export implementation bodies."""
    parent=EXP.parent/'exp-001-local-thinking-10/app-core-v07'
    root=Path(r'C:\Users\barkin\Documents\llm-bender-artifacts\tdd-v07-windows\sources')
    snapshots=read_json(parent/'source-snapshots.json');external=read_json(EXP/'external-app-audit.json')['sources']
    external_by_family={s['repository']:s for s in external}
    measured={};missing=[];mapping={}
    for row in test_rows:
        paths=[]
        if row['source_group'] in external_by_family:
            entry=external_by_family[row['source_group']];p=Path(entry['local_source'])/row['source']['source_file']
            paths=[(p,'pinned external module',row['source']['source_sha256'])]
        else:
            for relative in row['implementation_files']:
                local=parent/row['application']/'reference'/relative
                if local.exists():paths.append((local,'authored reference module',None));continue
                group=row['source_group'];expected=snapshots[group]['python_source_files']
                options=[(root/group/relative,relative),(root/group/'src'/relative,'src/'+relative)]
                found=next(((p,name) for p,name in options if p.exists() and name in expected),None)
                if found:paths.append((found[0],'pinned original module',expected[found[1]]))
                else:missing.append(dict(record_id=row['record_id'],declared_file=relative,reason='No direct file mapping; no guessed whole-repo substitute used.'))
        mapped=[]
        for path,scope,expected in paths:
            if not path.exists():missing.append(dict(record_id=row['record_id'],declared_file=str(path),reason='Local audit source unavailable'));continue
            hash=digest(path)
            if expected and hash!=expected:raise ValueError('Changed pinned reference source: '+str(path))
            key=str(path);mapped.append(key)
            if key not in measured:measured[key]=dict(path=key,source_group=row['source_group'],scope=scope,sha256=hash,metrics=complexity(path.read_text(encoding='utf-8')))
        mapping[row['record_id']]=mapped
    return dict(files=list(measured.values()),missing_mappings=missing,record_file_mapping=mapping,
                policy='Audit-only module statistics. No implementation text is saved or supplied to a model. Module metrics are not per-task solution complexity and repeated modules are counted once.')


def charts(out,records):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    train=[r for r in records if r['split']=='train'];colors=['#2563eb','#16a34a','#d97706']
    figure,axes=plt.subplots(2,2,figsize=(13,9),layout='constrained')
    groups=['tests','planning','reliability']
    axes[0,0].boxplot([[r['full_tokens'] for r in train if r['track']==track] for track in groups],tick_labels=groups)
    axes[0,0].set(title='Train-candidate sequence lengths',ylabel='Native tokens')
    axes[0,1].bar(groups,[sum(r['supervised_tokens'] for r in train if r['track']==t) for t in groups],color=colors)
    axes[0,1].set(title='Supervised-token exposure if each row is used once',ylabel='Tokens')
    domains=Counter(r['domain'] for r in train)
    axes[1,0].barh(list(domains),list(domains.values()),color='#64748b');axes[1,0].set(title='Train candidates by broad domain',xlabel='Rows')
    tests=[r for r in records if r['track']=='tests']
    axes[1,1].hist([f['cc_without_asserts'] for r in tests for f in r['complexity']['functions'] if f['kind']=='test'],bins=range(1,10),color='#2563eb',align='left')
    axes[1,1].set(title='Generated test-function CC, asserts excluded',xlabel='Cyclomatic complexity',ylabel='Functions')
    figure.savefig(out/'dataset-overview.svg');figure.savefig(out/'dataset-overview.png',dpi=160);plt.close(figure)


def dashboard(out,records):
    # Standalone, offline, filterable profile. No implementation text is included.
    payload=json.dumps([{k:r.get(k) for k in ['record_id','track','split','source_group','domain','subdomain','behavior','full_tokens','supervised_tokens','reasoning_tokens','test_cases','test_sloc','test_max_cc','test_max_cc_no_assert']} for r in records],ensure_ascii=False).replace('<','\\u003c')
    template='''<!doctype html><html><head><meta charset="utf-8"><title>TDD dataset profile</title><style>
body{font:15px system-ui;max-width:1400px;margin:30px auto;padding:0 20px;color:#172033;background:#f8fafc}h1{font-size:26px}select,input{padding:8px;margin:5px}section{background:white;border:1px solid #cbd5e1;border-radius:8px;padding:18px;margin:15px 0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.bar{display:flex;align-items:center;margin:8px 0}.bar span{width:180px}.bar b{display:block;background:#2563eb;height:17px;margin-right:8px}.note{color:#475569}table{border-collapse:collapse;width:100%;font-size:12px}td,th{border-bottom:1px solid #e2e8f0;padding:7px;text-align:left}th{position:sticky;top:0;background:#f1f5f9}.scroll{max-height:550px;overflow:auto}
</style></head><body><h1>Intent-driven TDD dataset profile</h1><p class="note">95 candidates / 78 train-family candidates. Not a trained model. Test CC describes generated tests, not application complexity. Source implementation is audit-only.</p>
<section><label>Track <select id="track"><option value="">All</option><option>tests</option><option>planning</option><option>reliability</option></select></label><label>Split <select id="split"><option value="">All</option><option selected>train</option><option>development</option><option>holdout</option></select></label><label>Search <input id="query" placeholder="Family, domain or task"></label><p id="summary"></p><div class="grid"><div><h3>Rows by domain</h3><div id="domainBars"></div></div><div><h3>Supervised tokens by track</h3><div id="tokenBars"></div></div></div></section>
<section><div class="scroll"><table><thead><tr><th>ID</th><th>Split</th><th>Domain</th><th>Behavior</th><th>Full tokens</th><th>Loss tokens</th><th>Cases</th><th>Test SLOC</th><th>Max CC</th><th>CC w/o asserts</th></tr></thead><tbody id="table"></tbody></table></div></section>
<p class="note">Full tokens include prompt and target. Loss tokens follow the audited native mask. Complexity is N/A for planning/decision records. Population standard deviation is used. The broader JSON/Markdown report contains methods, limitations and duplicate review.</p>
<script>const data=PAYLOAD;const $=id=>document.getElementById(id);function bars(id,counts){const root=$(id);root.replaceChildren();const max=Math.max(1,...Object.values(counts));for(const [name,value] of Object.entries(counts)){const row=document.createElement('div');row.className='bar';const label=document.createElement('span');label.textContent=name;const bar=document.createElement('b');bar.style.width=(value/max*240)+'px';const count=document.createElement('em');count.textContent=value.toLocaleString();row.append(label,bar,count);root.append(row)}}function render(){const selected=data.filter(r=>(!$('track').value||r.track===$('track').value)&&(!$('split').value||r.split===$('split').value)&&JSON.stringify(r).toLowerCase().includes($('query').value.toLowerCase()));const n=selected.length;const mean=n?selected.reduce((a,r)=>a+r.full_tokens,0)/n:0;const std=n?Math.sqrt(selected.reduce((a,r)=>a+(r.full_tokens-mean)**2,0)/n):0;$('summary').textContent=`${n} rows | full tokens mean ${mean.toFixed(1)}, population std ${std.toFixed(1)} | supervised total ${selected.reduce((a,r)=>a+r.supervised_tokens,0).toLocaleString()}`;const domains={},tokens={};for(const r of selected){domains[r.domain]=(domains[r.domain]||0)+1;tokens[r.track]=(tokens[r.track]||0)+r.supervised_tokens}$('table').replaceChildren();for(const r of selected){const tr=document.createElement('tr');for(const v of [r.record_id,r.split,r.domain,r.behavior,r.full_tokens,r.supervised_tokens,r.test_cases,r.test_sloc,r.test_max_cc,r.test_max_cc_no_assert]){const td=document.createElement('td');td.textContent=v??'N/A';tr.append(td)}$('table').append(tr)}bars('domainBars',domains);bars('tokenBars',tokens)}for(const id of ['track','split','query'])$(id).addEventListener('input',render);render();</script></body></html>'''
    save(out/'dashboard.html',template.replace('PAYLOAD',payload))


def main(args):
    out=inside(args.output)
    if out.exists():raise ValueError('Profile already exists; use a new output revision')
    paths=active_paths()
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(args.tokenizer,local_files_only=True,trust_remote_code=False)
    expected_pin=read_json(EXP/paths['config']['native_label_audit']).get('tokenizer_revision_verified')
    if not expected_pin:raise ValueError('Pinned tokenizer has not been verified')
    verification=read_json((EXP/paths['config']['native_label_audit']).parent/'tokenizer-pin-verification.json')
    for entry in verification['files']:
        if digest(Path(args.tokenizer)/entry['file'])!=entry['local_sha256']:raise ValueError('Tokenizer differs from audited snapshot')
    result=[];input_paths=[];test_rows=[]
    for track,path in [('tests',paths['tests']),('planning',paths['planning']),('reliability',paths['reliability'])]:
        input_paths.append(path)
        for row in rows(path):
            # The complexity/reference audit never contributes implementation code to this encoding.
            messages=[{k:v for k,v in m.items() if k in ('role','content','reasoning_content')} for m in row['messages']]
            encoded=encode_conversation(tokenizer,messages)
            broad,narrow=DOMAINS[row['source_group']]
            record=dict(record_id=row['record_id'],track=track,split=row['candidate_split'],source_group=row['source_group'],domain=broad,subdomain=narrow,
                        full_tokens=len(encoded['input_ids']),supervised_tokens=sum(x!=-100 for x in encoded['labels']),
                        ignored_tokens=sum(x==-100 for x in encoded['labels']),reasoning_tokens=len(encoded['region_positions']['reasoning']),
                        has_rationale=encoded['reasoning_present'],purpose=purpose(row,track),variant_of=row.get('variant_of'))
            if track=='tests':
                test_rows.append(row);record['behavior']=BEHAVIOR_BY_TASK[row['task_id']];record['source_behavior']=row.get('diversity',{}).get('behavior')
                record['complexity']=complexity(row['artifact']['content']);record['test_cases']=row['validation']['reference_cases']
                record['test_sloc']=record['complexity']['sloc'];record['test_max_cc']=max((f['cc'] for f in record['complexity']['functions']),default=0)
                record['test_max_cc_no_assert']=max((f['cc_without_asserts'] for f in record['complexity']['functions']),default=0)
                record['faults_detected']=sum(r.get('killed') is True for r in row['validation']['runs'])
                record['test_level']=row.get('diversity',{}).get('test_level','not annotated')
            elif track=='planning':
                plan=json.loads(row['messages'][-1]['content']);record['behavior']='app-decomposition';record['plan_tasks']=len(plan['tasks'])
                record['integration_todos']=sum(t['test_file'].startswith('tests/integration/') for t in plan['tasks'])
            else:
                target=json.loads(row['messages'][-1]['content']);record['behavior']=target['action'];record['decision_type']=row['record_type']
            result.append(record)
    out.mkdir()
    save(out/'records.jsonl',''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in result))
    columns=['record_id','track','split','source_group','domain','subdomain','behavior','full_tokens','supervised_tokens','ignored_tokens','reasoning_tokens','test_cases','test_sloc','test_max_cc','test_max_cc_no_assert']
    with (out/'records.csv').open('w',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=columns,extrasaction='ignore');writer.writeheader();writer.writerows(result)
    summary={}
    for split in ('all','train','development','holdout'):
        for track in ('all','tests','planning','reliability'):
            subset=[r for r in result if (split=='all' or r['split']==split) and (track=='all' or r['track']==track)]
            summary[split+'/'+track]={metric:stats([r[metric] for r in subset]) for metric in ('full_tokens','supervised_tokens','ignored_tokens','reasoning_tokens')}
    train=[r for r in result if r['split']=='train'];test=[r for r in result if r['track']=='tests']
    function_metrics=[f for r in test for f in r['complexity']['functions'] if f['kind']=='test']
    profile=dict(token_stats=summary,domains={split:diversity(Counter(r['domain'] for r in result if split=='all' or r['split']==split)) for split in ('all','train','development','holdout')},
                 source_families=diversity(Counter(r['source_group'] for r in result)),
                 behavior_types={split:diversity(Counter(r['behavior'] for r in test if split=='all' or r['split']==split)) for split in ('all','train')},
                 decision_actions=dict(Counter(r['behavior'] for r in result if r['track']=='reliability')),
                 test_code=dict(files=len(test),sloc=stats([r['test_sloc'] for r in test]),test_functions=len(function_metrics),
                                cc=stats([f['cc'] for f in function_metrics]),cc_without_asserts=stats([f['cc_without_asserts'] for f in function_metrics]),
                                cc_ranks=dict(Counter(f['cc_rank'] for f in function_metrics)),reference_cases=sum(r['test_cases'] for r in test),
                                targeted_faults_detected=sum(r['faults_detected'] for r in test),
                                imports=dict(Counter(module for r in test for module in r['complexity']['imports']))),
                 actual_agent_execution_training_rows=0,application_implementation_training_rows=0,planned_integration_todos=sum(r.get('integration_todos',0) for r in result),
                 supervised_share_if_all_train_rows_once={t:sum(r['supervised_tokens'] for r in train if r['track']==t)/sum(r['supervised_tokens'] for r in train) for t in ('tests','planning','reliability')})
    jsave(out/'summary.json',profile)
    reference=references(test_rows);jsave(out/'audit-only-reference-complexity.json',reference)
    similarity=similarities([r['purpose'] for r in result]);pairs=[]
    for score,i,j in similarity:
        a,b=result[i],result[j]
        pairs.append(dict(left=a['record_id'],right=b['record_id'],score=score,same_family=a['source_group']==b['source_group'],
                          cross_split=a['split']!=b['split'],same_track=a['track']==b['track'],left_track=a['track'],right_track=b['track']))
    jsave(out/'all-pair-similarities.json',pairs)
    cross=[p for p in pairs if p['cross_split']]
    review={}
    for key,subset,count in [('cross_split_same_track',[p for p in cross if p['same_track']],50),('cross_split_any_track',cross,30),
                              ('same_track_same_family',[p for p in pairs if p['same_track'] and p['same_family']],35),
                              ('different_family_same_track',[p for p in pairs if not p['same_family'] and p['same_track']],30)]:
        review[key]=subset[:count]
    jsave(out/'review-candidates.json',review)
    ids={r['record_id']:r for r in result};selected={tuple(sorted((p['left'],p['right']))) for group in review.values() for p in group}
    packet=[]
    for left,right in sorted(selected):
        a,b=ids[left],ids[right]
        packet.append(left+' ['+a['split']+', '+a['track']+']\n'+a['purpose']+'\n\nVERSUS\n'+right+' ['+b['split']+', '+b['track']+']\n'+b['purpose'])
    save(out/'semantic-review-packet.txt','\n----\n'.join(packet)+'\n')
    jsave(out/'manifest.json',dict(status='descriptive profile and candidate retrieval; semantic adjudication follows separately',records=len(result),
          methods=dict(tokens='Pinned native chat template and audited loss masks; all split targets measured for audit only.',
                       standard_deviation='Population std by default; sample std also saved. Percentiles use linear interpolation.',
                       complexity='Radon default CC counts assert as a decision; also measured with no_assert=True. Test functions only in primary CC summaries; helpers separately retained.',
                       similarity='Purpose/acceptance word+bigram sublinear TF-IDF cosine, system boilerplate and full repeated interfaces removed. Retrieval only, not embeddings or an automatic semantic verdict.',
                       domain='Explicit analyst mapping of 11 source families into 6 broad domains; not learned labels.',
                       reference_complexity='Audit-only direct module mappings, hash-checked for pinned source files. No implementation bodies saved.'),
          input_sha256={p.relative_to(EXP).as_posix():digest(p) for p in input_paths},
          code_sha256=digest(Path(__file__)),packages={p:importlib.metadata.version(p) for p in ['radon','matplotlib','transformers','tokenizers']},
          total_pairs=len(pairs),cross_split_pairs=len(cross),training_enabled=False))
    charts(out,result);dashboard(out,result)
    print(json.dumps(dict(records=len(result),train_rows=len(train),token_stats=summary['train/all'],test_code=profile['test_code']|{'imports':'see summary'},reference_modules=len(reference['files']),missing_reference_mappings=len(reference['missing_mappings']),top_cross_split=cross[:10]),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--tokenizer',required=True);parser.add_argument('--output',default='dataset-profile-v01')
    main(parser.parse_args())
