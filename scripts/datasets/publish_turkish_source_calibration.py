"""Create one new local Argilla calibration dataset, without replacing any data."""
import argparse
import json
import os
from pathlib import Path
import argilla as rg
from audit_turkish_sources import ROOT, OUT, filehash


def main():
    # Match the established local Compose credentials without logging secrets.
    env_path=ROOT/'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env'
    if env_path.exists():
        for line in env_path.read_text(encoding='utf-8-sig').splitlines():
            key,sep,value=line.partition('=')
            if sep and key.strip() in ['ARGILLA_API_KEY','ARGILLA_WORKSPACE']:
                os.environ.setdefault(key.strip(),value.strip().strip('"').strip("'"))
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-url',default=os.getenv('ARGILLA_API_URL','http://127.0.0.1:6900'))
    parser.add_argument('--workspace',default=os.getenv('ARGILLA_WORKSPACE','sft-review'))
    parser.add_argument('--name',default='turkish-sft-source-calibration-v01')
    args=parser.parse_args()
    packet=OUT/'review-local/calibration-60.jsonl'
    manifest=json.loads((OUT/'calibration-60-manifest.json').read_text())
    if filehash(packet)!=manifest['packet_sha256']:raise ValueError('Packet changed since frozen source manifest')
    rows=[json.loads(line) for line in packet.read_text(encoding='utf-8').splitlines()]
    if len(rows)!=60 or any(row['human_reviewed'] or row['training_eligible'] or row['source_split']!='train' for row in rows):
        raise ValueError('Expected 60 unapproved training-source review candidates')
    client=rg.Argilla(api_url=args.api_url,api_key=os.getenv('ARGILLA_API_KEY','argilla.apikey'))
    workspace=client.workspaces(name=args.workspace)
    if workspace is None:raise ValueError('Expected existing local review workspace')
    if client.datasets(name=args.name,workspace=args.workspace) is not None:
        raise FileExistsError('Dataset already exists; preserve its reviews rather than replace it')
    settings=rg.Settings(
      guidelines='Review calibration only: these 60 source records include good, repairable and unusable examples. Judge the supplied task and system instruction; do not reward brevity or length alone. Check correctness, grounding, Turkish, required format and completeness. For reasoning, check BOTH steps and final answer. Choose keep/edit/reject/unsure. For edit, provide a complete corrected answer and, if necessary, corrected user prompt. For CoT edits the corrected answer must include BOTH the corrected worked solution and final answer, clearly separated. Do not submit an edit with only a note. Provenance/release eligibility is a separate audit; keeping content is not training approval. No agent decisions are prefilled.',
      fields=[rg.TextField(name='source',title='Source and immutable row identity'),
        rg.TextField(name='system',title='Original system instruction',required=False),
        rg.TextField(name='conversation',title='Original conversation before final assistant'),
        rg.TextField(name='worked_solution',title='Original worked solution (when parsable)',required=False),
        rg.TextField(name='answer',title='Original final answer / proposed target')],
      questions=[rg.LabelQuestion(name='decision',title='Content decision',labels=['keep','edit','reject','unsure']),
        rg.LabelQuestion(name='correctness',title='Correct and grounded?',labels=['pass','fail','unsure']),
        rg.LabelQuestion(name='instruction',title='Follows the requested task and format?',labels=['pass','fail','unsure']),
        rg.LabelQuestion(name='turkish',title='Turkish quality',labels=['good','needs_edit','poor'],required=False),
        rg.LabelQuestion(name='detail',title='Amount of detail',labels=['appropriate','too_short','too_long'],required=False),
        rg.TextQuestion(name='corrected_answer',title='Complete corrected answer (for edit)',required=False),
        rg.TextQuestion(name='corrected_user',title='Corrected user prompt (only if needed)',required=False),
        rg.TextQuestion(name='notes',title='Notes / error evidence',required=False)],
      metadata=[rg.TermsMetadataProperty(name='source_key',options=['occam','sft','atlas','cot'])])
    records=[]
    for row in rows:
        ms=row['original_messages'];answer=ms[-1]['content'];reason=''
        if ms[-1]['role']!='assistant':raise ValueError('Missing final assistant target')
        if answer.startswith('<think>') and answer.count('<think>')==answer.count('</think>')==1:
            reason,answer=answer[len('<think>'):].split('</think>',1)
            reason=reason.strip();answer=answer.strip()
        source_key=row['id'].split(':',1)[0]
        records.append(rg.Record(id=row['id'],fields=dict(
            source=row['source_repo']+' @ '+row['source_revision']+'\n'+row['source_filename']+':'+str(row['source_line_1based']),
            system='\n'.join(m['content'] for m in ms if m['role']=='system'),
            conversation='\n\n'.join(m['role'].upper()+':\n'+m['content'] for m in ms[:-1] if m['role']!='system'),
            worked_solution=reason,answer=answer),metadata=dict(source_key=source_key)))
    dataset=rg.Dataset(name=args.name,workspace=args.workspace,settings=settings,client=client)
    dataset.create();dataset.records.log(records,batch_size=20)
    count=len(list(dataset.records))
    if count!=60:raise ValueError(f'Partial upload: {count}/60. Preserve and inspect before retrying.')
    receipt=dict(dataset_name=args.name,dataset_id=str(dataset.id),workspace=args.workspace,
       url=args.api_url+'/dataset/'+str(dataset.id)+'/annotation-mode',records=count,
       packet_sha256=filehash(packet),publisher_sha256=filehash(Path(__file__)),
       owner_submissions_at_creation=0,note='New dataset only; no existing datasets deleted or replaced. No labels or suggestions prefilled.')
    (OUT/'argilla-calibration-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
