import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from active_tdd_data import EXP,active_paths,rows
from run_tdd_demo_gpu import collate,verify_preflight


def test_frozen_inputs_and_no_evaluation_rows_in_training():
    preflight=EXP/'demo-preflight-v01'
    config=verify_preflight(preflight)
    train=rows(preflight/'train-encoded.jsonl')
    requests=rows(preflight/'development-requests.jsonl')
    source={r['record_id']:r for r in rows(active_paths()['tests'])}
    assert len(train)==50
    assert all(source[r['record_id']]['candidate_split']=='train' for r in train)
    assert all(r['split']=='development' and [m['role'] for m in r['messages']]==['system','user'] for r in requests)
    assert not {r['record_id'] for r in train}&{r['record_id'] for r in requests}
    assert max(len(r['input_ids']) for r in train)<=config['training']['max_seq_length']
    assert sum(len(r['input_ids']) for r in train)==91858


def test_collator_preserves_masked_prompt_and_real_eos_even_when_pad_equals_eos():
    first=dict(input_ids=[1,2,9],attention_mask=[1,1,1],labels=[-100,2,9])
    second=dict(input_ids=[3,9],attention_mask=[1,1],labels=[-100,9])
    result=collate([first,second],pad_id=9)
    assert result['labels']==[[-100,2,9],[-100,9,-100]]
    assert result['attention_mask']==[[1,1,1],[1,1,0]]
    assert result['input_ids']==[[1,2,9],[3,9,9]]
