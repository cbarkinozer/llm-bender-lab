"""CPU-only audit and freeze for original-base -> CPT -> CPT+SFT inference."""
import collections
from datetime import datetime,timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/turkish-capability/lfm3-1.7b'
OUT=BASE/'stage-diagnostic-v01'
RUNTIME=BASE/'stage-diagnostic-v01-local'
TRAIN=BASE/'bilingual-pilot-v01/revisions/v01-corrections-02/train.jsonl'
TOKENIZER=BASE/'bilingual-runtime-local/native/exp-011-bilingual-sft640/tokenizer'
ADAPTER=BASE/'exp-011-bilingual-sft640/results-local/sft/checkpoint-69'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
def write(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert p.read_bytes()==data,('Immutable output differs',str(p))
    else:p.write_bytes(data)
def dump(p,v):write(p,(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n').encode())
def jsonl(p,rs):write(p,(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rs)).encode())

def build():
    from tokenizers import Tokenizer
    from validate_lfm3_bilingual_pilot import arith_checks,number_multiset
    assert sha(TRAIN)=='17170506a2510bf938cf196dc08f79729334e267fd1b6b8a718e56b82f499db6'
    rs=rows(TRAIN);assert len(rs)==640 and len({r['id'] for r in rs})==640
    groups={}
    for r in rs:
        groups.setdefault(r['group_id'],{})[r['direction']]=r
        assert r['split']=='train' and [m['role'] for m in r['messages']]==['system','user','assistant']
        assert all(m['content'].strip() for m in r['messages'])
        assert r['has_reasoning']==bool(r['worked_solution'])
        text=json.dumps([r['messages'],r['worked_solution']],ensure_ascii=False)
        assert not any(tag in text for tag in ['<think>','</think>','<thinking>','</thinking>','<|im_start|>','<|im_end|>'])
    assert len(groups)==160 and all(set(g)=={'tr-tr','en-tr','tr-en','en-en'} for g in groups.values())
    alignment=[]
    for gid,g in groups.items():
        for a,b in [('tr-tr','en-tr'),('tr-en','en-en')]:
            assert g[a]['messages'][-1]['content']==g[b]['messages'][-1]['content'],(gid,a,b)
            assert g[a]['worked_solution']==g[b]['worked_solution'],(gid,'reasoning')
        # Input suffixes intentionally differ with requested target language.
        for a,b in [('tr-tr','tr-en'),('en-tr','en-en')]:
            assert g[a]['messages'][1]['content'].rsplit('\n\n',1)[0]==g[b]['messages'][1]['content'].rsplit('\n\n',1)[0]
        if g['tr-en'].get('output_language_effect')!='full':alignment.append(gid)
    tok=Tokenizer.from_file(str(TOKENIZER/'tokenizer.json'))
    sys.path.insert(0,str(ROOT/'scripts/training'))
    from run_lfm3_bilingual_pilot import render
    lens=[];reason_lens=[];all_targets=[];short=[]
    for r in rs:
        prefix,full=render(r['messages'],r['worked_solution']);ids=tok.encode(full,add_special_tokens=False).ids;pids=tok.encode(prefix,add_special_tokens=False).ids
        assert ids[:len(pids)]==pids and 124900 in ids[len(pids):] and len(ids)<=4096
        lens.append(len(ids));target=len(ids)-len(pids);all_targets.append(target)
        reason_lens.append(len(tok.encode(r['worked_solution'] or '',add_special_tokens=False).ids))
        if target<=32:short.append(r['id'])
    checks=[]
    for gid,(calculation,expected) in arith_checks().items():
        g=groups['bp01-'+gid]
        checks.append(dict(group_id='bp01-'+gid,computed=calculation,
            verification_scope='Independently recomputed reference quantities; number presence is coverage only, NOT semantic/constraint proof.',
            directions={direction:dict(expected_numeric_markers=expected,
                missing_markers=[n for n in expected if str(Decimal(n).normalize()) not in number_multiset(r['messages'][-1]['content']+'\n'+(r['worked_solution'] or ''),r['output_language'])]) for direction,r in g.items()}))
    dump(OUT/'arithmetic-reference-audit.json',checks)
    direct_math=[r['group_id'] for r in rs if r['direction']=='tr-tr' and r['category']=='arithmetic_and_constraints' and not r['worked_solution']]
    order=json.loads((TRAIN.parent/'token-budget-and-order.json').read_text())['order_b'][:69*8]
    summary=dict(train_sha256=sha(TRAIN),rows=640,groups=160,directions=dict(collections.Counter(r['direction'] for r in rs)),
        category_groups=dict(collections.Counter(r['category'] for r in rs if r['direction']=='tr-tr')),
        reasoning_rows=sum(bool(r['worked_solution']) for r in rs),direct_rows=sum(not r['worked_solution'] for r in rs),
        explicit_reasoning_tokens=sum(reason_lens),supervised_tokens_one_pass=sum(all_targets),max_sequence_tokens=max(lens),
        short_target_rows_le32=len(short),short_target_ids=short,direct_math_group_ids=direct_math,
        primary69=dict(row_slots=len(order),reasoning_row_slots=sum(bool(rs[i]['worked_solution']) for i in order),
            supervised_tokens=sum(all_targets[i] for i in order),explicit_reasoning_tokens=sum(reason_lens[i] for i in order)),
        arithmetic_reference_groups=len(checks),numeric_marker_findings=sum(bool(d['missing_markers']) for c in checks for d in c['directions'].values()),
        language_bound_groups=alignment,raw_thinking_markup_rows=0,structural_status='passed',
        limitations=['This is not a complete semantic or external fact-check of640 answers.',
            'Existing quantitative reference functions reused; numeric presence is not correctness.',
            'No training data or owner reviews were changed. Known corrected ambiguities remain explicit.'])
    dump(OUT/'training-audit.json',summary)
    packet=BASE/'bilingual-pilot-v01/eval-v01';evaluation=rows(packet/'eval-prompts.jsonl');refs=rows(packet/'eval-references.jsonl')
    rng=random.Random(3407);selected=[]
    for category in sorted({r['category'] for r in evaluation}):
        candidates=sorted({r['group_id'] for r in evaluation if r['category']==category})
        selected+=candidates if category=='arithmetic' else rng.sample(candidates,1)
    diagnostic=[dict(r,cohort='consumed-eval-diagnostic') for r in evaluation if r['group_id'] in selected]
    symbolic=[dict(r,cohort='consumed-symbolic-diagnostic') for r in rows(packet/'symbolic-controls-prompts.jsonl')]
    training=[];training_refs=[]
    for gid in ['bp01-g014','bp01-g116','bp01-g131']:
        for direction,r in groups[gid].items():
            ident='seen-'+r['id'];training.append(dict(id=ident,group_id=gid,direction=direction,
                category=r['category'],messages=r['messages'][:-1],cohort='seen-training-probe',
                evaluation_only=True,training_allowed=False,interpretation='SFT saw this exact row; measures fitting/retention, NEVER generalization'))
            training_refs.append(dict(id=ident,source_row_id=r['id'],reference_answer=r['messages'][-1]['content'],
                worked_solution=r['worked_solution'],cohort='seen-training-probe'))
    main=diagnostic+symbolic+training;thinking=symbolic+[dict(r,cohort='consumed-thinking-diagnostic') for r in evaluation if r['category']=='arithmetic' and r['direction']=='tr-tr']
    assert len(diagnostic)==52 and len(main)==72 and len(thinking)==16
    assert len({r['id'] for r in main})==72
    for r in main+thinking:
        assert [m['role'] for m in r['messages']] in [['system','user'],['user']] and r['training_allowed'] is False
        prefix='<|startoftext|>'+''.join('<|im_start|>'+m['role']+'\n'+m['content']+'<|im_end|>\n' for m in r['messages'])+'<|im_start|>assistant\n<think></think>'
        assert len(tok.encode(prefix,add_special_tokens=False).ids)+4096<=8192
    jsonl(OUT/'prompts.jsonl',main);jsonl(OUT/'thinking-prompts.jsonl',thinking)
    selected_ids={r['id'] for r in main+thinking}
    references=[r for r in refs+rows(packet/'symbolic-controls-references.jsonl') if r['id'] in selected_ids]+training_refs
    jsonl(OUT/'references-local-only.jsonl',references)
    dump(OUT/'packet-manifest.json',dict(status='frozen-diagnostic-not-fresh-test',main_rows=72,thinking_rows=16,
        expected_outputs=264,selected_groups=selected,selection='All8 arithmetic groups, Random(3407) one group per other category; four directions per group. Plus8 symbolic and12 seen-training probes.',
        models=['base','cpt','cpt-bilingual69'],main_thinking=False,secondary_thinking=True,
        stage_interpretation='Same exact ancestry for CPT->SFT; exp013 is not a CPT descendant and cannot isolate this transition.',
        references_sha256=sha(OUT/'references-local-only.jsonl'),training_probes_are_seen=True))

def freeze():
    files=[OUT/n for n in ['prompts.jsonl','thinking-prompts.jsonl','packet-manifest.json','training-audit.json']]
    files += [ROOT/p for p in ['scripts/evaluation/run_lfm3_stage_diagnostic.py','scripts/evaluation/evaluate_lfm3_vllm_batched.py',
        'scripts/training/download_lfm3_session.py','scripts/training/setup_lfm3_stage_diagnostic.sh','scripts/evaluation/run_lfm3_stage_diagnostic.sh','scripts/datasets/prepare_lfm3_stage_diagnostic.py']]
    files += [ADAPTER/'adapter_config.json',ADAPTER/'adapter_model.safetensors',BASE/'exp-000-baseline/config-planned.json']
    assert sha(ADAPTER/'adapter_model.safetensors')=='580b7a5392475a5821e415f118913dd7125de832bc302d83f1d8d700dbf7a974'
    target=OUT/'freeze.json'
    stable=dict(models=['base','cpt','cpt-bilingual69'],base_revision='0dc4268b561499c648c7ba7c9466bf3d8d01517a',
        cpt_revision='6f213ec25a944dab2fbdeb6d337deb0e0442e638',sft_checkpoint=69,
        decoding=dict(seed=3407,temperature=.1,top_k=50,top_p=1.,repetition_penalty=1.1,max_new_tokens=4096,max_model_len=8192,batch_size=4,stop_token_ids=[124900]),
        training_authorized=False,outputs=264,references_local_only_sha256=sha(OUT/'references-local-only.jsonl'),
        files={p.relative_to(ROOT).as_posix():sha(p) for p in files})
    if target.exists():
        old=json.loads(target.read_text(encoding='utf-8'))
        assert all(old[k]==v for k,v in stable.items()),'Never change a frozen run';return
    dump(target,dict(stable,created_utc=datetime.now(timezone.utc).isoformat(),git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),git_dirty=True))
    RUNTIME.mkdir(exist_ok=True)
    with tarfile.open(RUNTIME/'pod-input.tar.gz','w:gz') as t:
        for p in files+[target]:t.add(p,arcname=p.relative_to(ROOT))
    dump(OUT/'bundle-receipt.json',dict(archive='stage-diagnostic-v01-local/pod-input.tar.gz',bytes=(RUNTIME/'pod-input.tar.gz').stat().st_size,
        sha256=sha(RUNTIME/'pod-input.tar.gz'),freeze_sha256=sha(target),contains_references=False,contains_training_code=False,contains_full_weights=False))

if __name__=='__main__':
    build();freeze();print(json.dumps(json.loads((OUT/'bundle-receipt.json').read_text()),indent=2))
