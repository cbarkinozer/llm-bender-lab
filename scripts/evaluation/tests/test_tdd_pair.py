from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from active_tdd_data import EXP,rows,read_json
from prepare_tdd_pair import inference_identity
from run_tdd_demo_gpu import verify_preflight,gate_identity_matches,causal_token_loss
from prepare_tdd_demo import digest


def test_only_rationale_labels_differ_and_counts_are_exact():
    root=EXP/'paired-preflight-v01'
    a=rows(root/'A/train-encoded.jsonl');b=rows(root/'B/train-encoded.jsonl')
    assert len(a)==len(b)==50
    removed=0
    for first,second in zip(a,b):
        assert first['record_id']==second['record_id']
        assert first['input_ids']==second['input_ids'] and first['attention_mask']==second['attention_mask']
        for old,new in zip(first['labels'],second['labels']):
            assert new==old or (old!=-100 and new==-100)
            removed+=new!=old
        assert [x for x in first['labels'] if x in (248046,)]==[x for x in second['labels'] if x in (248046,)]
    assert removed==1419
    assert sum(sum(x!=-100 for x in r['labels']) for r in a)==17266
    assert sum(sum(x!=-100 for x in r['labels']) for r in b)==15847


def test_baseline_shared_but_training_gates_cannot_cross_arms():
    root=EXP/'paired-preflight-v01';a=verify_preflight(root/'A');b=verify_preflight(root/'B')
    assert a['inference']['repetition_penalty']==b['inference']['repetition_penalty']==1.15
    identity=inference_identity(root/'A',a)
    assert identity==inference_identity(root/'B',b)
    assert gate_identity_matches(dict(inference_identity=identity),'baseline',root/'B',b)
    assert not gate_identity_matches(dict(recipe_sha256=digest(root/'A/recipe.json')),'smoke',root/'B',b)
    assert gate_identity_matches(dict(recipe_sha256=digest(root/'B/recipe.json')),'smoke',root/'B',b)


def test_accumulation_loss_and_gradients_equal_global_token_mean():
    import torch
    import torch.nn.functional as F
    torch.manual_seed(42)
    logits=torch.randn(2,4,5,requires_grad=True)
    labels=torch.tensor([[-100,1,2,3],[-100,-100,4,0]])
    count=int((labels[:,1:]!=-100).sum())
    expected=F.cross_entropy(logits[:,:-1,:].reshape(-1,5),labels[:,1:].reshape(-1),ignore_index=-100)
    actual=sum(causal_token_loss(dict(logits=logits[i:i+1]),labels[i:i+1],count) for i in range(2))
    torch.testing.assert_close(actual,expected)
    first=torch.autograd.grad(actual,logits,retain_graph=True)[0]
    second=torch.autograd.grad(expected,logits)[0]
    torch.testing.assert_close(first,second)


def test_actual_cpu_trainer_supplies_accumulation_group_count(tmp_path):
    import torch
    from copy import deepcopy
    from transformers import Trainer,TrainingArguments
    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__();self.embedding=torch.nn.Embedding(8,4);self.output=torch.nn.Linear(4,8)
        def forward(self,input_ids,attention_mask=None):return dict(logits=self.output(self.embedding(input_ids)))
    dataset=[dict(input_ids=[1,2,3],attention_mask=[1,1,1],labels=[-100,2,3]),
             dict(input_ids=[4,5,6],attention_mask=[1,1,1],labels=[-100,-100,6])]
    seen=[]
    def loss(outputs,labels,num_items_in_batch=None):
        seen.append(int(num_items_in_batch));return causal_token_loss(outputs,labels,num_items_in_batch)
    model=Tiny();expected=deepcopy(model)
    batch=torch.tensor([r['input_ids'] for r in dataset]);targets=torch.tensor([r['labels'] for r in dataset])
    causal_token_loss(expected(batch),targets).backward()
    with torch.no_grad():
        for parameter in expected.parameters():parameter.add_(parameter.grad,alpha=-.1)
    trainer=Trainer(model=model,args=TrainingArguments(output_dir=str(tmp_path),use_cpu=True,report_to=[],
        per_device_train_batch_size=1,gradient_accumulation_steps=2,max_steps=1,save_strategy='no',disable_tqdm=True,remove_unused_columns=False,
        optim='sgd',learning_rate=.1,lr_scheduler_type='constant',max_grad_norm=0,weight_decay=0),
        train_dataset=dataset,compute_loss_func=loss)
    trainer.train()
    assert seen==[3,3]
    for actual,reference in zip(model.parameters(),expected.parameters()):torch.testing.assert_close(actual,reference)
