import csv
from pathlib import Path
import argilla as rg

ROOT = Path(__file__).parent
CSV = ROOT / 'results' / 'benchmark-v2-blind-review' / 'argilla-review.csv'
NAME = 'exp-004-v2-blind-benchmark'
WORKSPACE = 'sft-review'
client = rg.Argilla(api_url='http://127.0.0.1:6900', api_key='argilla.apikey')
old = client.datasets(name=NAME, workspace=WORKSPACE)
if old is not None:
    old.delete()
settings = rg.Settings(
    guidelines='Blind paired review. Do not infer which output is base or LoRA. Judge output A and B only against the prompt and the stated policy.',
    fields=[
        rg.TextField(name='category', title='Capability category', use_markdown=False),
        rg.TextField(name='prompt_tr', title='Prompt', use_markdown=False),
        rg.TextField(name='output_a', title='Output A', use_markdown=False),
        rg.TextField(name='output_b', title='Output B', use_markdown=False),
        rg.TextField(name='automatic_diagnostics', title='Automatic diagnostics', use_markdown=False),
    ],
    questions=[
        rg.LabelQuestion(name='pairwise_preference', title='Which response is better overall?', labels=['a','b','tie'], required=True),
        rg.LabelQuestion(name='task_completion_a', title='A: task completion', labels=['pass','fail'], required=True),
        rg.LabelQuestion(name='task_completion_b', title='B: task completion', labels=['pass','fail'], required=True),
        rg.LabelQuestion(name='directness_a', title='A: directness', labels=['pass','fail'], required=True),
        rg.LabelQuestion(name='directness_b', title='B: directness', labels=['pass','fail'], required=True),
        rg.LabelQuestion(name='neutrality_a', title='A: neutrality', labels=['pass','fail'], required=True),
        rg.LabelQuestion(name='neutrality_b', title='B: neutrality', labels=['pass','fail'], required=True),
        rg.LabelQuestion(name='helpfulness_a', title='A: helpfulness', labels=['pass','fail'], required=True),
        rg.LabelQuestion(name='helpfulness_b', title='B: helpfulness', labels=['pass','fail'], required=True),
        rg.LabelQuestion(name='calibration_a', title='A: calibration', labels=['pass','fail'], required=True),
        rg.LabelQuestion(name='calibration_b', title='B: calibration', labels=['pass','fail'], required=True),
        rg.LabelQuestion(name='clarification_discipline_a', title='A: clarification discipline', labels=['pass','fail','not_applicable'], required=True),
        rg.LabelQuestion(name='clarification_discipline_b', title='B: clarification discipline', labels=['pass','fail','not_applicable'], required=True),
        rg.LabelQuestion(name='non_anthropomorphism_a', title='A: non-anthropomorphism', labels=['pass','fail','not_applicable'], required=True),
        rg.LabelQuestion(name='non_anthropomorphism_b', title='B: non-anthropomorphism', labels=['pass','fail','not_applicable'], required=True),
        rg.TextQuestion(name='review_notes', title='Review notes', required=False, use_markdown=False),
    ],
)
dataset = rg.Dataset(name=NAME, workspace=WORKSPACE, settings=settings, client=client)
dataset.create()
records=[]
with CSV.open(encoding='utf-8-sig', newline='') as f:
    for row in csv.DictReader(f):
        diag = '; '.join(f'{k}={row[k]}' for k in ('shorter_output','output_a_chars','output_b_chars','auto_a_social_preamble','auto_b_social_preamble','auto_a_anthropomorphic_claim','auto_b_anthropomorphic_claim') if k in row)
        records.append(rg.Record(id=row['id'], fields={'category':row['category'],'prompt_tr':row['prompt_tr'],'output_a':row['output_a'],'output_b':row['output_b'],'automatic_diagnostics':diag}))
dataset.records.log(records, batch_size=25)
print(f'{NAME} records={len(records)} url=http://127.0.0.1:6900/dataset/{dataset.id}/annotation-mode?page=1&status=pending')
