"""Owner-approved matched fast screening; preserve the historical 500-item runs."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def main():
    root = Path('experiments/turkish-capability/lfm3-1.7b')
    protocol = json.loads((root/'cpt-eval-fast100-v02.json').read_text())
    os.environ.update(HF_HOME='/workspace/.cache/huggingface',PYTHONUNBUFFERED='1')
    py = '/workspace/.venvs/lfm3/bin/python'
    v = '/workspace/.venvs/lfm3-vllm/bin/python'
    control = root/'preparation-local/fast100-v02'
    control.mkdir(parents=True,exist_ok=False)

    def run(cmd, name):
        started = time.time()
        with (control/(name+'.log')).open('w') as stream:
            result = subprocess.run([str(x) for x in cmd],stdout=stream,stderr=subprocess.STDOUT)
        with (control/'commands.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(command=[str(x) for x in cmd],start_unix=started,
                seconds=time.time()-started,exit_code=result.returncode,log=name+'.log'))+'\n')
        if result.returncode:
            raise RuntimeError('Failed stage: '+name)
        print(name+' completed',flush=True)

    b = root/'exp-002-mixed-cpt'
    for task in ['text','turblimp']:
        run([py,f'scripts/evaluation/evaluate_lfm3_{task}.py','--experiment-dir',b,
            '--output-dir',b/'results-local/cpt-eval-v01'/task,'--adapter',b/'results-local/cpt-v01/adapter'],
            'mixed-'+task)
    results = {}
    canonical = None
    for name, folder in [('exp-000-baseline','base-v01'),('exp-001-wiki-cpt','cpt-eval-v01'),('exp-002-mixed-cpt','cpt-eval-v01')]:
        exp = root/name
        output = exp/'results-local/fast100-v02/cetvel'
        cmd = [v,'scripts/evaluation/evaluate_lfm3_vllm_batched.py','--experiment-dir',exp,
            '--output-dir',output,'--limit','100','--batch-size','4','--repetition-penalty','1.15']
        if name != 'exp-000-baseline':
            cmd += ['--merged-model',exp/'results-local/cpt-v01/merged-model']
        run(cmd,name+'-generation')
        run([py,'scripts/evaluation/score_lfm3_cetvel.py','--results-dir',output],name+'-scoring')
        manifest = json.loads((output/'manifest.json').read_text())
        rows = [json.loads(s) for s in (output/'answers.jsonl').read_text(encoding='utf-8').splitlines()]
        assert manifest['status']=='completed' and manifest['count']==len(rows)==100
        assert manifest['selected_ids']==protocol['selected_ids']
        assert set(r['id'] for r in rows)==set(protocol['selected_ids'])
        assert Counter(r['task'] for r in rows)==dict.fromkeys(Counter(r['task'] for r in rows),20)
        if canonical is None:
            canonical = manifest
        else:
            for key in ['questions_sha256','selected_ids','decoding','packages','chat_template_sha256','eos_token_ids','seed']:
                assert canonical[key]==manifest[key], 'Matched protocol failed: '+key
            for key in ['dtype','max_model_len','gpu_memory_utilization','enforce_eager','max_num_seqs','enable_prefix_caching']:
                assert canonical['engine_args'][key]==manifest['engine_args'][key]
        scores = json.loads((output/'scores.json').read_text())
        primary = exp/'results-local'/folder
        text = json.loads((primary/'text/text-scores.json').read_text())
        grammar = json.loads((primary/'turblimp/scores.json').read_text())
        results[name] = dict(cetvel=scores['results'],termination=scores['termination'],
            text={k:{field:v[field] for field in ['nll','perplexity','scored_tokens','source_sha256']} for k,v in text['results'].items()},
            grammar_macro_accuracy=grammar['macro_accuracy'],generation_wall_seconds=manifest['wall_seconds'],
            generated_tokens=sum(r['generated_tokens'] for r in rows),empty_outputs=sum(not r['prediction'].strip() for r in rows),
            mean_generated_tokens=sum(r['generated_tokens'] for r in rows)/100,
            answers_sha256=hashlib.sha256((output/'answers.jsonl').read_bytes()).hexdigest())
    report = dict(status='matched_fast100_completed',protocol=protocol,results=results,
        caveats=['Exploratory 20 items per task; not a final 500-item claim.',
            'New penalty 1.15 and batching protocol; do not compare these CETVEL scores with rp1.05 scores.',
            'NLL/grammar retain the original likelihood protocol, unaffected by generation repetition penalty.',
            'All length/loop/timeout outputs retained; exact answer equivalence across batch sizes is not claimed.'])
    (root/'cpt-fast100-results-v02.json').write_text(json.dumps(report,indent=2)+'\n')
    print('MATCHED_FAST100_COMPLETED',flush=True)


if __name__=='__main__':
    main()
