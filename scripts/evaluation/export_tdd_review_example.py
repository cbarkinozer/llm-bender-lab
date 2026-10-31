"""Export one complete example with blank annotation options and fault evidence."""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DEFAULT=ROOT/'experiments/unit-test-generation/qwen3.5-4b/exp-001-local-thinking-10/app-core-v06'


def build_text(row, form, guidelines):
    parts=[row['record_id'],'','MODEL INPUT','','SYSTEM:',row['messages'][0]['content'],
           '','USER:',row['messages'][1]['content'],'','OUTPUT TO REVIEW','',
           'CONCISE RATIONALE:',row['teacher_reasoning'],'','FINAL RESPONSE:',row['messages'][2]['content'],
           '','REVIEW-ONLY EVIDENCE — NOT MODEL INPUT OR OUTPUT','',
           'Source app: '+row['source']['repo']+'; revision: '+row['source']['revision'],
           'Split: '+row['split']+'; leakage group: '+row['leakage_group'],
           'Reference suite: '+('PASS' if row['validation']['reference_pass'] else 'FAIL'),
           'Full native sequence: '+str(row['tokens']['full_sequence'])+' / 8192 tokens.',
           'Passing shuffled-order seeds: '+', '.join(str(s['seed']) for s in row['validation']['stability']),
           '','TARGETED KILLS BY CORE REQUIREMENT']
    faults={f['fault']:f for f in row['validation']['faults']}
    for rid,names in row['validation']['fault_coverage_by_core_requirement'].items():
        assert names, 'Missing fault evidence for '+rid
        parts.append(rid+':')
        for name in names:
            fault=faults[name]
            parts.append('  '+name+' — '+('DETECTED' if fault['killed'] else 'SURVIVED'))
            parts.extend('    failing test: '+test for test in fault['failing_tests'])
    parts += ['','Fault probes are targeted evidence, not exhaustive coverage. A strong assertion can still be wrong.',
              'Original source and grading evidence are not part of the model messages.',
              '','ANNOTATION FORM — BLANK','No answers are prefilled.']
    for q in form:
        parts += ['',q['title']]
        if q['options']:parts += ['Options: '+' | '.join(q['options'])]
        if q['kind']=='multi-select':parts += ['Select all that apply.']
        if q['required']:parts += ['Required.']
        parts += ['Answer: ______________________________']
    parts += ['','ANNOTATION GUIDELINES',guidelines]
    return '\n'.join(parts).rstrip('\n')+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,default=DEFAULT)
    parser.add_argument('--record',default='codelang-detect')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    row=json.loads((args.bundle/args.record/'record.json').read_text(encoding='utf-8'))
    forms=list(args.bundle.glob('human-review-*/presentation-v02/annotation-options.json'))
    assert len(forms)==1,'Publish the bundle once to freeze its actual annotation options.'
    form=json.loads(forms[0].read_text(encoding='utf-8'))
    text=build_text(row,form,(forms[0].parent/'GUIDELINES.md').read_text(encoding='utf-8'))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text, encoding='utf-8', newline='\n')
    print(json.dumps(dict(file=str(args.output),record=row['record_id'],questions=len(form),faults=len(row['validation']['faults']),characters=len(text)),indent=2))

if __name__=='__main__':main()
