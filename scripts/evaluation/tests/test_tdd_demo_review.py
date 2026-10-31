import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from active_tdd_data import EXP,rows
from run_tdd_demo_gpu import verified_stop_ids,verify_preflight
from review_tdd_demo_outputs import extract_test,pair_review,functions,verify_generation_pair
from prepare_tdd_demo import save,digest
from grade_tdd_demo_protected import classify


def output(code='def test_ok():\n    assert 1 == 1\n'):
    return dict(finish_reason='stop',text='secret reasoning</think>\nFile: tests/test_ok.py\n```python\n'+code+'```')


def test_parser_never_grades_thinking_or_truncated_code():
    row=output();assert extract_test(row)['status']=='complete_parseable'
    assert 'secret' not in extract_test(row)['code']
    assert extract_test(dict(row,finish_reason='length'))['code'] is None
    assert extract_test(dict(row,text=row['text'].replace('</think>','')))['code'] is None
    assert extract_test(dict(row,text=row['text'].replace('tests/test_ok.py','../escape.py')))['code'] is None


def test_blinded_pairs_hide_role_and_rationale_and_keep_unusable_rows(tmp_path):
    req=tmp_path/'req.jsonl';base=tmp_path/'base.jsonl';candidate=tmp_path/'candidate.jsonl'
    req.write_text(json.dumps(dict(record_id='a',capability='task-to-tests',messages=[{},dict(content='requirements')]))+'\n')
    base.write_text(json.dumps(dict(record_id='a',**output()))+'\n')
    candidate.write_text(json.dumps(dict(record_id='a',**dict(output(),finish_reason='length')))+'\n')
    dest=tmp_path/'review';pair_review(base,candidate,dest,req)
    packet=(dest/'review-packet.jsonl').read_text()
    assert 'secret reasoning' not in packet and 'baseline' not in packet and 'candidate' not in packet
    assert 'No complete parseable' in packet and 'tie / both_unusable' in packet
    assert len(rows(dest/'review-packet.jsonl'))==1
    assert len(json.loads((dest/'completion-accounting.json').read_text()))==2


def test_stop_ids_are_verified_against_actual_tokenizer_mapping():
    class Tokenizer:
        unk_token_id=None;eos_token_id=10
        def convert_tokens_to_ids(self,token):return {'<|im_end|>':10,'<|endoftext|>':20}[token]
        def encode(self,token,**kw):return [self.convert_tokens_to_ids(token)]
    assert verified_stop_ids(Tokenizer(),[10,20])==[10,20]
    with pytest.raises(ValueError):verified_stop_ids(Tokenizer(),[248046,248044])


def report(returncode=0,outcome='passed',assertion=False,when='call'):
    return dict(returncode=returncode,order=['test_generated.py::test_ok'],
                reports=[dict(nodeid='test_generated.py::test_ok',outcome=outcome,assertion=assertion,when=when)])


def test_fault_credit_requires_reference_pass_and_real_assertion():
    good=report();fault=report(1,'failed',True)
    assert classify(good,fault)
    assert not classify(report(1,'failed',True),fault)
    assert not classify(good,report(1,'failed',False))
    assert not classify(good,report(1,'failed',True,'setup'))
    assert not classify(report(0,'skipped'),fault)
    assert not classify(good,dict(fault,order=[]))


def test_review_revision_keeps_training_identical_and_holdout_closed():
    old=verify_preflight(EXP/'demo-preflight-v01');new=verify_preflight(EXP/'demo-preflight-v02')
    assert old['training']==new['training']
    assert new['inference']['max_tokens']==4096
    assert (EXP/'demo-preflight-v01/train-encoded.jsonl').read_bytes()==(EXP/'demo-preflight-v02/train-encoded.jsonl').read_bytes()
    assert all(r['split']=='development' for r in rows(EXP/'demo-preflight-v02/development-requests.jsonl'))
    assert all(extract_test(r)['code'] for r in rows(EXP/'demo-preflight-v02/executor-reference-controls.jsonl'))


def test_upstream_ast_screen_ignores_test_name_but_keeps_assertion_semantics():
    a=functions('def test_first():\n assert x == 1\n')[0]['ast_sha256']
    b=functions('def test_second():\n assert x == 1\n')[0]['ast_sha256']
    c=functions('def test_second():\n assert x == 2\n')[0]['ast_sha256']
    assert a==b and a!=c


def test_pairing_rejects_different_runtime_or_changed_outputs(tmp_path):
    base=tmp_path/'base';candidate=tmp_path/'candidate';base.mkdir();candidate.mkdir()
    for path,stage in ((base,'baseline'),(candidate,'candidate')):
        (path/'outputs.jsonl').write_text('{}\n')
        save(path/'result.json',dict(stage=stage,recipe_sha256='recipe',runtime_lock_sha256='runtime',outputs_sha256=digest(path/'outputs.jsonl')))
    verify_generation_pair(base/'outputs.jsonl',candidate/'outputs.jsonl')
    result=json.loads((candidate/'result.json').read_text());result['runtime_lock_sha256']='different';save(candidate/'result.json',result)
    with pytest.raises(ValueError):verify_generation_pair(base/'outputs.jsonl',candidate/'outputs.jsonl')
    result['runtime_lock_sha256']='runtime';save(candidate/'result.json',result)
    (candidate/'outputs.jsonl').write_text('{"changed":true}\n')
    with pytest.raises(ValueError):verify_generation_pair(base/'outputs.jsonl',candidate/'outputs.jsonl')


def test_revision_builder_reproduces_saved_recipe_and_arrays(tmp_path,monkeypatch):
    import shutil
    import revise_tdd_demo_protocol as revision
    shutil.copytree(EXP/'demo-preflight-v01',tmp_path/'demo-preflight-v01')
    monkeypatch.setattr(revision,'EXP',tmp_path)
    revision.main()
    for name in ('recipe.json','train-encoded.jsonl','development-requests.jsonl','executor-reference-controls.jsonl'):
        assert (tmp_path/'demo-preflight-v02'/name).read_bytes()==(EXP/'demo-preflight-v02'/name).read_bytes()
