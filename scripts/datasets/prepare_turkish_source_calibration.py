"""Create an unapproved 60-record source-review packet, never a training export."""
from collections import Counter
import json
import random
from pathlib import Path
from audit_turkish_sources import OUT, SOURCES, messages, filehash, digest, norm


def main():
    destination=OUT/'review-local/calibration-60.jsonl'
    if destination.exists():raise FileExistsError('Preserve existing calibration packet; create a new version for edits')
    selected=[]
    for key,(repo,revision,_) in SOURCES.items():
        rows=[json.loads(line) for line in (OUT/'review-local'/(key+'-samples.jsonl')).read_text(encoding='utf-8').splitlines()]
        rows=[row for row in rows if row['source_split']=='train']
        if key=='cot':
            wanted=[1,48,73,148,173,198,223,247,269,294,466,677,2002,2144,3336]
            by_line={row['line']:row for row in rows}
            choices=[by_line[line] for line in wanted]
        elif key=='occam':
            grouped={}
            for row in rows:grouped.setdefault(row['original']['category'],[]).append(row)
            choices=[]
            for group in grouped.values():choices.append(group[0])
            leftovers=[row for row in rows if row not in choices]
            random.Random(3407).shuffle(leftovers);choices=(choices+leftovers)[:15]
        else:
            ordered=sorted(rows,key=lambda row:row['answer_characters'])
            # Spread across the audit sample's observed length range; not population sampling.
            choices=[ordered[round(i*(len(ordered)-1)/14)] for i in range(15)]
        for row in choices:
            original=row['original'];ms=messages(original)
            selected.append(dict(id=row['id'],source_repo=repo,source_revision=revision,
                 source_filename=row['filename'],source_line_1based=row['line'],source_row_id=row['source_row_id'],
                 original_messages=ms,source_category=original.get('category',original.get('alan')),
                 original_record_sha256=digest(json.dumps(original,ensure_ascii=False,sort_keys=True)),
                 source_prompt_sha256=row['prompt_sha256'],source_answer_sha256=row['answer_sha256'],
                 source_split='train',reserved_use='training-candidate-review-only',
                 review_status='pending',human_reviewed=False,training_eligible=False,
                 owner_decision=None,corrected_answer=None,owner_notes=None,
                 provenance_status='source-audit-provisional; not a training/release clearance'))
    if len(selected)!=60 or len({r['id'] for r in selected})!=60:raise ValueError('Expected exactly 60 unique candidates')
    if len({r['source_prompt_sha256'] for r in selected})!=60:raise ValueError('Duplicate prompts in calibration')
    destination.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in selected),encoding='utf-8')
    manifest=dict(n=60,source_counts=dict(Counter(row['source_repo'] for row in selected)),
        analyzer_sha256=filehash(Path(__file__)),
        cot_domain_counts=dict(Counter(row['source_category'] for row in selected if 'CoT' in row['source_repo'])),
        packet_path='review-local/calibration-60.jsonl',packet_sha256=filehash(destination),
        accepted=0,human_reviewed=0,selection='15/source. Occam category coverage; SFT/Atlas audit-sample length spread; CoT reviewer shortlist spanning 13 domains. Includes keep/edit/reject possibilities, not a best-60 selection.',
        exclusions=['All source validation rows excluded.','Known benchmark-derived items may not be accepted.'],
        intended_use='Owner rubric calibration in Argilla next; no training use or approval inferred.',
        source_ids=[row['id'] for row in selected])
    (OUT/'calibration-60-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Prepared 60 unapproved review records; zero validation rows; zero accepted records.')


if __name__=='__main__':main()
