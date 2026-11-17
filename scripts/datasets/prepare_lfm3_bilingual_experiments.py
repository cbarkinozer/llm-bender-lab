"""(Re)write exp-010 / exp-011 config.yaml (JSON) from exp-007's actual config + the token-budget plan. Planning only."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bilingual_pilot_common import BASE, PILOT

D = 'experiments/turkish-capability/lfm3-1.7b/bilingual-pilot-v01'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()  # noqa: E731


def make(base, plan, eid, arm):
    c = json.loads(json.dumps(base))
    c['status'] = 'planned'
    c['experiment'].update(id=eid, parent='exp-007-sft160-lr1e4',
                           comparison_variable='training data composition only (Turkish-only vs four-direction bilingual) at matched supervised-token exposure',
                           initialization='Independent fresh LoRA on the SAME pinned CPT-merged parent; never resume exp-007 adapters')
    a = plan[arm]
    src = 'data/train-arm-a-tr-only.jsonl' if arm == 'arm_a' else 'data/train.jsonl'
    c['dataset'] = dict(directory=D, train_file=f'{D}/{src}', train_sha256=sha(PILOT / src), train_rows=a['rows'],
                        build_manifest_sha256=sha(PILOT / 'build-manifest.json'), eval_directory=f'{D}/eval-v01',
                        eval_manifest_sha256=sha(PILOT / 'eval-v01/manifest.json'),
                        schema='messages + worked_solution (reasoning separate); native template applied at preprocessing',
                        target_policy='assistant target and end-of-turn only; blank thinking for direct answers unchanged (exp-007 parity)',
                        data_order_file=f'{D}/plan/token-budget-and-order.json', data_order_key='order_a' if arm == 'arm_a' else 'order_b',
                        use_restriction=('none from provider terms (Turkish originals + short instruction only); source eligibility still open'
                                         if arm == 'arm_a' else 'RESTRICTED_PENDING_PROVIDER_TERMS: contains agent translations'),
                        gate='plan/gates.json must mark every gate true (runner refuses otherwise)')
    t = c['training']
    t.update(epochs=None, optimizer_steps=a['optimizer_steps'], expected_optimizer_steps=a['optimizer_steps'],
             supervised_token_budget=a['supervised_tokens_total'], epochs_equivalent=a.get('epochs_equivalent', 5),
             data_order='explicit per-epoch permutation (random.Random(3407+epoch)), one sequential pass, no shuffling',
             runner='scripts/training/run_lfm3_bilingual_pilot.py', save_steps=a['checkpoint_steps'], warmup_steps=6,
             checkpoint_selection='Pre-registered: choose between the two saved checkpoints on dev20 + crosslingual-holdout-v01 + CETVEL100/TurBLiMP (NOT eval-v01); earlier checkpoint on practical ties; eval-v01 scored once afterwards.')
    c['evaluation']['cohorts'] = ['Independent dev20; selection only', 'crosslingual-holdout-v01 (12+3); development/regression',
                                  'CETVEL100 + TurBLiMP1600 regression', 'eval-v01 35 tasks x 4 directions + 8 symbolic: fresh, scored once, never for selection',
                                  'English retention, stopping/EOS/loop counts, formatting (numeric-only, bullets, JSON)']
    c['tracking']['group'] = 'lfm3-turkish-bilingual-pilot-v01'
    c['tracking']['run_name'] = ('exp010-tr-only-sft160-lr1e-4-100step-r32' if arm == 'arm_a' else 'exp011-bilingual-sft640-lr1e-4-112step-r32')
    c['preflight']['required'] = base['preflight']['required'] + [
        'validate_lfm3_bilingual_pilot.py + eval freeze check', 'CPU audit: run_lfm3_bilingual_pilot.py --mode audit (done) repeated in the GPU environment',
        'Decide --mask-empty-think (default off = exp-007 parity)', 'Owner answers UNRESOLVED-DECISIONS']
    return c


def main():
    base = json.loads((BASE / 'exp-007-sft160-lr1e4/config.yaml').read_text(encoding='utf-8'))
    plan = json.loads((PILOT / 'plan/token-budget-and-order.json').read_text(encoding='utf-8'))
    for eid, arm in (('exp-010-tr-only-sft160', 'arm_a'), ('exp-011-bilingual-sft640', 'arm_b')):
        (BASE / eid).mkdir(exist_ok=True)
        (BASE / eid / 'config.yaml').write_text(json.dumps(make(base, plan, eid, arm), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('configs written')


main()
