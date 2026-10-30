"""Blind review for original Occam32 under four model/thinking conditions."""
import argparse
import collections
import json
from pathlib import Path
import random

from pipeline import sha, write_json, read_rows
from occam_matrix import benchmark, SOURCE_HASHES, SOURCES

CONDITIONS = ['base-thinking-false','base-thinking-true','occam1-thinking-false','occam1-thinking-true']


def positions(ids):
    rng=random.Random(3407)
    shuffled=list(ids)
    rng.shuffle(shuffled)
    order=CONDITIONS.copy()
    rng.shuffle(order)
    return {identity:dict(zip('ABCD',order[index%4:]+order[:index%4])) for index,identity in enumerate(shuffled)}


def prepare(work, output, recovery=None):
    if output.exists():
        raise ValueError('Review folder exists; preserve prior ratings')
    manifest=json.loads((work/'matrix-manifest.json').read_text())
    if not manifest['complete'] or manifest['completed']!=128:
        raise ValueError('Wait for all four conditions/32 items before preparing the review')
    if manifest['outputs_sha256']!=sha(work/'outputs.jsonl'):
        raise ValueError('Recorded outputs changed')
    if manifest['provenance']['source_sha256']!=dict(zip(SOURCES,SOURCE_HASHES)):
        raise ValueError('Original benchmark identity mismatch')
    outputs=read_rows(work/'outputs.jsonl')
    by_key={(r['condition'],r['id']):r for r in outputs}
    prompts,keys=benchmark()
    if len(by_key)!=128 or set(by_key)!={(c,p['id']) for c in CONDITIONS for p in prompts}:
        raise ValueError('Missing or duplicate paired condition IDs')
    recovery_provenance=None
    if recovery is not None:
        recovered_manifest=json.loads((recovery/'recovery-manifest.json').read_text())
        if not recovered_manifest['complete'] or recovered_manifest['error'] is not None:
            raise ValueError('Budget recovery must finish before preparing an updated review')
        if recovered_manifest['provenance']['original_manifest_sha256']!=sha(work/'matrix-manifest.json'):
            raise ValueError('Recovery belongs to a different original matrix')
        if recovered_manifest['outputs_sha256']!=sha(recovery/'outputs.jsonl'):
            raise ValueError('Recovery outputs changed')
        for row in read_rows(recovery/'outputs.jsonl'):
            key=row['condition'],row['id']
            if key not in by_key or not row['thinking']:
                raise ValueError('Recovery contains an unexpected condition/item')
            by_key[key]=row
        recovery_provenance=dict(manifest_sha256=sha(recovery/'recovery-manifest.json'),
            outputs_sha256=sha(recovery/'outputs.jsonl'),
            interpretation=('Uniform16384-token/context20480 rerun of all64 thinking-on responses; original thinking-off outputs retained.'
                if recovered_manifest['provenance']['budgets']==[16384]
                   and len(recovered_manifest['provenance']['selected'])==64 else
                'Adaptive budget recovery, not a uniform higher-budget benchmark. Original non-limited outputs retained.'))
    mapping=positions([p['id'] for p in prompts])
    reference={r['id']:r for r in keys}
    records=[]
    for prompt in prompts:
        identity=prompt['id']
        row=dict(id=identity,cohort=prompt['cohort'],messages=prompt['messages'],
                 reference=reference[identity]['reference'],criteria=reference[identity]['evaluation_criteria'])
        if identity=='me-089':
            row['rubric_note']='Retain historical rubric sensitivity: do not require a fixed single-sentence emotional reflection; report aggregate with and without this item.'
        for position,condition in mapping[identity].items():
            r=by_key[condition,identity]
            row[position]=dict(answer=r['answer'],reasoning=r['reasoning'],
                termination=r['response']['stop_type'],output_tokens=r['response']['tokens_predicted'],
                output_allowance=r['request']['n_predict'],
                grade=None,notes='')
        records.append(row)
    output.mkdir(parents=True)
    write_json(output/'ratings.json',records)
    write_json(output/'private-mapping.json',mapping)
    write_json(output/'provenance.json',dict(outputs_sha256=sha(work/'outputs.jsonl'),
        matrix_manifest_sha256=sha(work/'matrix-manifest.json'),
        recovery=recovery_provenance,
        reviewer_policy='Keep mapping hidden. Pass/partial/fail uses original semantic correctness/usefulness rubric. New outputs require review; no inherited grades.',
        limitation='Thinking length and answer style can reveal conditions despite hidden model labels; one reviewer is not independent inter-rater evidence.'))


def summarize(folder):
    rows=json.loads((folder/'ratings.json').read_text())
    mapping=json.loads((folder/'private-mapping.json').read_text())
    expected={r['id'] for r in benchmark()[0]}
    if len(rows)!=32 or {r['id'] for r in rows}!=expected or set(mapping)!=expected:
        raise ValueError('All32 original IDs must be reviewed')
    for row in rows:
        if set(mapping[row['id']].values())!=set(CONDITIONS):
            raise ValueError('Invalid condition mapping')
        for position in 'ABCD':
            if row[position]['grade'] not in ('pass','partial','fail'):
                raise ValueError(f'Unrated: {row["id"]}/{position}')
    result={}
    for cohort in ('original20','controls12','all32','all32-without-me089'):
        selected=[r for r in rows if r['cohort']==cohort or cohort=='all32' or
                  (cohort=='all32-without-me089' and r['id']!='me-089')]
        counts={c:collections.Counter() for c in CONDITIONS}
        for row in selected:
            for pos,condition in mapping[row['id']].items():
                counts[condition][row[pos]['grade']]+=1
        paired={}
        for before,after in [('base-thinking-false','base-thinking-true'),
                             ('occam1-thinking-false','occam1-thinking-true'),
                             ('base-thinking-false','occam1-thinking-false'),
                             ('base-thinking-true','occam1-thinking-true')]:
            outcomes=collections.Counter()
            changes=[]
            for row in selected:
                grades={condition:row[pos]['grade'] for pos,condition in mapping[row['id']].items()}
                a,b=grades[before],grades[after]
                # Strict full-pass transitions; partial-versus-fail is recorded but
                # not mislabeled as a fixed full-correctness question.
                outcomes['fixed' if a!='pass' and b=='pass' else
                         'regressed' if a=='pass' and b!='pass' else 'same_full_pass_status']+=1
                if a!=b:changes.append(dict(id=row['id'],before=a,after=b))
            paired[f'{before} -> {after}']=dict(outcomes=outcomes,grade_changes=changes)
        result[cohort]=dict(items=len(selected),counts=counts,paired=paired)
    write_json(folder/'summary.json',dict(results=result,
        limitation='Historical development/regression benchmark; not a fresh holdout or broad Turkish accuracy estimate.'))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    create=sub.add_parser('prepare');create.add_argument('--work',required=True,type=Path);create.add_argument('--output',required=True,type=Path)
    create.add_argument('--recovery',type=Path)
    summary=sub.add_parser('summarize');summary.add_argument('--review',required=True,type=Path)
    args=p.parse_args()
    if args.command=='prepare':prepare(args.work,args.output,args.recovery)
    else:summarize(args.review)
