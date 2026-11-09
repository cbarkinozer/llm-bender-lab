"""Guard the experimental intervention, not generated test execution."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from active_tdd_data import EXP, rows
from run_tdd_demo_gpu import verify_preflight, gate_identity_matches
from prepare_tdd_demo import digest
from prepare_tdd_pair import inference_identity
from audit_tdd_pair_run import verify_training_arguments
import pytest


def test_lr_pair_preserves_original_thinking_labels_and_only_changes_rate():
    root=EXP/'lr-pair-preflight-v01'
    original=EXP/'paired-preflight-v02/A/train-encoded.jsonl'
    configs=[]
    for name,rate in [('Exp3',1e-5),('Exp4',3e-5)]:
        folder=root/name;config=verify_preflight(folder)
        assert (folder/'train-encoded.jsonl').read_bytes()==original.read_bytes()
        assert config['arm']=='A' and config['training']['loss_policy']=='rationale-supervised'
        assert sum(sum(x!=-100 for x in r['labels']) for r in rows(folder/'train-encoded.jsonl'))==17266
        assert config['training'].pop('learning_rate')==rate
        config.pop('experiment_id');configs.append(config)
    assert configs[0]==configs[1]


def test_new_eval_cannot_reuse_old_baseline_or_other_rate_training_gates():
    old=EXP/'paired-preflight-v02/A';root=EXP/'lr-pair-preflight-v01'
    first=verify_preflight(root/'Exp3');second=verify_preflight(root/'Exp4')
    identity=inference_identity(root/'Exp3',first)
    assert identity==inference_identity(root/'Exp4',second)
    assert not gate_identity_matches(dict(inference_identity=inference_identity(old,verify_preflight(old))),
                                     'baseline',root/'Exp3',first)
    assert not gate_identity_matches(dict(recipe_sha256=digest(root/'Exp3/recipe.json')),
                                     'smoke',root/'Exp4',second)


def test_saved_runtime_arguments_cannot_silently_use_other_learning_rate():
    recipe=verify_preflight(EXP/'lr-pair-preflight-v01/Exp3');t=recipe['training']
    actual=dict(learning_rate=1e-5,num_train_epochs=3,per_device_train_batch_size=1,
        gradient_accumulation_steps=8,seed=3407,data_seed=3407,warmup_steps=2,weight_decay=0,
        max_grad_norm=1,optim='adamw_8bit',lr_scheduler_type='cosine',bf16=True,fp16=False)
    verify_training_arguments(actual,recipe)
    actual['learning_rate']=3e-5
    with pytest.raises(ValueError,match='learning_rate'):verify_training_arguments(actual,recipe)
