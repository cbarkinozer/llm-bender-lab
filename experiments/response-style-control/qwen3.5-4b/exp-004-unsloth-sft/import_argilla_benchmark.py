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
    guidelines='Blind paired review. Do not infer which output is base or LoRA. Read the prompt and choose only the better response overall. Use Equal when neither is clearly better. Add a note only when it explains an important decision.',
    fields=[
        rg.TextField(name='category', title='Capability category', use_markdown=False),
        rg.TextField(name='prompt_tr', title='Prompt', use_markdown=False),
        rg.TextField(name='output_a', title='Output A', use_markdown=False),
        rg.TextField(name='output_b', title='Output B', use_markdown=False),
    ],
    questions=[
        rg.LabelQuestion(name='pairwise_preference', title='Which response is better overall?', labels=['A','B','Equal'], required=True),
        rg.TextQuestion(name='review_notes', title='Optional note (only for an important issue)', required=False, use_markdown=False),
    ],
)
dataset = rg.Dataset(name=NAME, workspace=WORKSPACE, settings=settings, client=client)
dataset.create()
records=[]
with CSV.open(encoding='utf-8-sig', newline='') as f:
    for row in csv.DictReader(f):
        records.append(rg.Record(id=row['id'], fields={'category':row['category'],'prompt_tr':row['prompt_tr'],'output_a':row['output_a'],'output_b':row['output_b']}))
dataset.records.log(records, batch_size=25)
print(f'{NAME} records={len(records)} url=http://127.0.0.1:6900/dataset/{dataset.id}/annotation-mode?page=1&status=pending')
