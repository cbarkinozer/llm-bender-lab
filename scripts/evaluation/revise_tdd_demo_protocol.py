"""Reproduce the v02 evaluation revision without changing training arrays."""
import shutil
from active_tdd_data import EXP,active_paths,read_json,rows
from prepare_tdd_demo import save,lines,digest


def main():
    src=EXP/'demo-preflight-v01';out=EXP/'demo-preflight-v02'
    if out.exists():raise ValueError('Preserve existing v02')
    out.mkdir()
    for name in ('train-encoded.jsonl','development-encoded.jsonl','development-requests.jsonl','development-targets.jsonl'):
        shutil.copyfile(src/name,out/name)
    r=read_json(src/'recipe.json');r['inference'].update(max_tokens=4096,max_num_seqs=1,enable_chunked_prefill=False,runtime_lock_required=True)
    r['evaluation'].update(
        primary='Joint evidence: correct-reference passes and targeted-fault detection plus blinded semantic assertion/requirement review',
        scope='Requirement-to-pytest generation under explicit task specifications; families excluded from our SFT, unknown pretraining overlap',
        pretraining_contamination='Public repository/test exposure in base weights is unknown. Screen generated development tests for upstream similarity; absence of matches does not prove independence.',
        completion='Report all-task completed/parseable/useful counts, and separately conditional completed-pair semantic review. Never silently drop truncations.',
        baseline_headroom='Inspect base outputs and protected execution results before full training; record proceed/stop rationale',
        review='Hide rationale; randomize pair sides; allow tie/both unusable; keep mapping private; record reviewer independence',
        seeds='One initial training seed3407. Optional second seed3408 if promising/ambiguous, requiring a separate frozen recipe and gates. Additional seeds do not increase evaluation-family diversity.',
        execution='Network-disabled resource-limited Docker only. Correct-reference pass required for mutant credit; assertion failures only, no import/collection errors. Curated fault coverage is incomplete.',
        hardware='RTX4090 24GB remote; local GTX1650 4GB is not supported')
    save(out/'recipe.json',r)
    controls=[dict(record_id=row['record_id'],finish_reason='stop',text='</think>\n\n'+row['messages'][-1]['content'],audit_only=True)
              for row in rows(active_paths()['tests']) if row['candidate_split']=='development']
    lines(out/'executor-reference-controls.jsonl',controls)
    save(out/'baseline-review-template.json',dict(baseline_outputs_sha256='FILL_FROM_ACTUAL_RUN',outputs_inspected=False,
         proceed_with_diagnostic=False,reason='',execution_summary='',headroom_notes='',reviewer=''))
    m=read_json(src/'manifest.json');m['status']='revised local preflight; Docker and GPU validation pending'
    m['files']={p.name:digest(p) for p in out.iterdir()};m['supersedes']='demo-preflight-v01 protocol only; training data and arrays unchanged'
    save(out/'manifest.json',m)


if __name__=='__main__':main()
