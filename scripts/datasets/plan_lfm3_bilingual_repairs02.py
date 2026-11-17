"""Retarget unrun experiments to corrected data; recompute matched token exposure."""
import copy
import json
import random
from pathlib import Path

from apply_lfm3_bilingual_repairs02 import BASE, DEST, PILOT, ROOT, save, sha


def order(n):
    indices = []
    for epoch in range(5):
        perm = list(range(n))
        random.Random(3407 + epoch).shuffle(perm)
        indices.extend(perm)
    return indices


def main():
    rows = [json.loads(l) for l in (DEST/'train.jsonl').read_text(encoding='utf-8').splitlines()]
    tokens = {r['id']: r for r in json.loads((DEST/'row-token-lengths.json').read_text(encoding='utf-8'))}
    a = [r for r in rows if r['direction'] == 'tr-tr']
    oa, ob = order(160), order(640)

    def cumulative(selected, indices):
        total, result = 0, []
        for start in range(0, len(indices), 8):
            total += sum(tokens[selected[i]['id']]['supervised'] for i in indices[start:start+8])
            result.append(total)
        return result

    ca, cb = cumulative(a, oa), cumulative(rows, ob)
    target = ca[99]
    steps_b = min(range(80, 201), key=lambda s: abs(cb[s-1]-target))
    # Preserve historical A step60 and match its actual token exposure in B.
    checkpoint_b = min(range(1, steps_b), key=lambda s: abs(cb[s-1]-ca[59]))
    plan = dict(status='planned; no training', seed=3407, batch_rows_per_step=8,
        order_a=oa[:800], order_b=ob[:steps_b*8],
        arm_a=dict(rows=160, optimizer_steps=100, checkpoint_steps=[60,100], supervised_tokens_total=target),
        arm_b=dict(rows=640, optimizer_steps=steps_b, checkpoint_steps=[checkpoint_b,steps_b],
                   supervised_tokens_total=cb[steps_b-1], supervised_vs_arm_a=cb[steps_b-1]/target-1),
        checkpoint_policy='A step60/100 unchanged; B checkpoints nearest A actual cumulative supervised-token exposure',
        unavoidable_differences=['Unique language variants and per-direction exposure differ.',
            'Optimizer update counts and cosine horizon differ; warmup remains six steps.',
            'Row-batch granularity prevents exact equality of supervised tokens; masked-context exposure also differs.'],
        inputs={'train_sha256':sha(DEST/'train.jsonl'), 'row_lengths_sha256':sha(DEST/'row-token-lengths.json')})
    save(DEST/'token-budget-and-order.json',plan)
    for exp, arm, filename, key in [
        ('exp-010-tr-only-sft160',plan['arm_a'],'train-arm-a-tr-only.jsonl','order_a'),
        ('exp-011-bilingual-sft640',plan['arm_b'],'train.jsonl','order_b')]:
        path = BASE/exp/'config.yaml'
        cfg = json.loads(path.read_text(encoding='utf-8'))
        backup = DEST/'previous-plans'/exp/'config.yaml'
        if not backup.exists():
            save(backup,cfg)
        cfg['dataset'].update(directory=DEST.relative_to(ROOT).as_posix(),
            train_file=(DEST/filename).relative_to(ROOT).as_posix(), train_sha256=sha(DEST/filename),
            build_manifest_sha256=sha(DEST/'corrections.json'),
            build_manifest_file=(DEST/'corrections.json').relative_to(ROOT).as_posix(),
            data_order_file=(DEST/'token-budget-and-order.json').relative_to(ROOT).as_posix(),data_order_key=key)
        cfg['training'].update(expected_optimizer_steps=arm['optimizer_steps'], optimizer_steps=arm['optimizer_steps'],
            save_steps=arm['checkpoint_steps'], supervised_token_budget=arm['supervised_tokens_total'],
            epochs_equivalent=arm['optimizer_steps']*8/arm['rows'])
        cfg['dataset']['use_restriction']='Preserve existing owner-accepted private research decision; source eligibility gate unchanged. Revised English text includes owner-authorized assistant repairs.'
        cfg['experiment']['dataset_revision']='v01-corrections-02'
        save(path,cfg)
    save(PILOT/'ACTIVE-REVISION.json',dict(revision='v01-corrections-02', directory=DEST.relative_to(ROOT).as_posix(),
        train_sha256=sha(DEST/'train.jsonl'), tr_only_sha256=sha(DEST/'train-arm-a-tr-only.jsonl'),
        note='Use corrected revision; original data and v01-corrections-01 remain immutable. No training started.'))
    validation = json.loads((DEST/'validation.json').read_text(encoding='utf-8'))
    validation['experiment_configs_retargeted'] = True
    validation['token_budget_plan_sha256'] = sha(DEST/'token-budget-and-order.json')
    validation['limitations'] = [s for s in validation['limitations'] if not s.startswith('Old experiment configs')]
    save(DEST/'validation.json',validation)
    print(json.dumps({k:plan[k] for k in ('arm_a','arm_b')},indent=2))


if __name__ == '__main__':
    main()
