"""Completed matched LFM CPT pair: separate metrics and seeded full answers."""
import argparse
from collections import Counter
import hashlib
import html
import json
from pathlib import Path
import random
import statistics


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model-root', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    a = p.parse_args()
    read = lambda path: json.loads(path.read_text(encoding='utf-8'))
    runs = [('Original', 'exp-000-baseline', 'base-v01'),
            ('Wiki 2.2M CPT', 'exp-001-wiki-cpt', 'cpt-eval-v01'),
            ('Wiki + FineWeb 10M CPT', 'exp-002-mixed-cpt', 'cpt-eval-v01')]
    data, hashes = [], {}
    for label, name, folder in runs:
        root = a.model_root/name/'results-local'/folder
        manifest = read(root/'cetvel/manifest.json')
        if manifest['status'] != 'completed' or manifest['count'] != 500:
            raise ValueError('Incomplete generation run: ' + name)
        rows = [json.loads(s) for s in (root/'cetvel/answers.jsonl').read_text(encoding='utf-8').splitlines()]
        if len(rows) != 500 or len({r['id'] for r in rows}) != 500:
            raise ValueError('Missing/duplicate answers')
        for file in [root/'cetvel/answers.jsonl', root/'cetvel/scores.json', root/'text/text-scores.json', root/'turblimp/scores.json']:
            hashes[str(file.relative_to(a.model_root))] = hashlib.sha256(file.read_bytes()).hexdigest()
        if folder != 'base-v01':
            if read(a.model_root/name/'results-local/comparison-v01.json')['status'] != 'matched_comparison_completed':
                raise ValueError('Strict protocol comparison has not passed')
        data.append(dict(label=label, rows=rows, scores=read(root/'cetvel/scores.json')['results'],
            text=read(root/'text/text-scores.json')['results'], grammar=read(root/'turblimp/scores.json')))
    for run in data[1:]:
        for base, other in zip(data[0]['rows'], run['rows']):
            for key in ['id', 'task', 'semantic_prompt', 'document_sha256', 'target']:
                if base[key] != other[key]:
                    raise ValueError('Paired item identity mismatch: ' + key)
    metrics = []
    for split, label in [('wiki_eval', 'Wikipedia NLL (lower better)'), ('web_eval', 'FineWeb NLL (lower better)')]:
        metrics.append((label, [r['text'][split]['nll'] for r in data]))
        metrics.append((label.replace('NLL', 'perplexity'), [r['text'][split]['perplexity'] for r in data]))
    metrics.append(('TurBLiMP macro accuracy (%)', [r['grammar']['macro_accuracy']*100 for r in data]))
    for label, task, key, scale in [('GEC exact correction (%)','gecturk','exact_match_rate',100),
            ('TQUAD F1 (%)','tquad','f1',100), ('XQuAD F1 (%)','xquad_tr','f1',100),
            ('EN to TR BLEU','wmt_en_tr','corpus_bleu',1), ('EN to TR chrF','wmt_en_tr','corpus_chrf',1),
            ('MLSum ROUGE-L (%)','mlsum_tr','mean_rougeL',100)]:
        metrics.append((label, [r['scores'][task][key]*scale for r in data]))
    metrics += [('Mean generated tokens', [statistics.mean(x['generated_tokens'] for x in r['rows']) for r in data]),
                ('Mean answer characters', [statistics.mean(len(x['prediction']) for x in r['rows']) for r in data])]
    caveats = ['Exploratory, one seed. No pooled score or statistically established superiority.',
        'The mixed recipe changes token count, web content and optimizer updates together.',
        'Same frozen packets and decoding. Original benchmark ran on an earlier pod/driver; bitwise reproducibility is not claimed.',
        'CETVEL was inspected historically and public pretraining contamination cannot be ruled out.',
        'Overlap metrics reward answer format and length as well as content; shorter answers are not necessarily more correct.',
        'No matched English retention evaluation. Web eval is now same-source held-out.',
        'Examples use Random(3407), one per task, chosen from original IDs without looking at new answers. Full prompts and answers are shown.']
    lines = ['LFM3 TURKISH CPT PAIR', '', *caveats, '', 'Metric | ' + ' | '.join(r['label'] for r in data)]
    lines += [label + ' | ' + ' | '.join(f'{x:.4f}' for x in values) for label, values in metrics]
    health = {r['label']:dict(Counter(x['finish_reason'] for x in r['rows'])) for r in data}
    lines += ['', 'Termination: ' + json.dumps(health), '']
    esc = html.escape
    body = '<h1>LFM3 Turkish CPT pair</h1><ul>'+''.join('<li>'+esc(s)+'</li>' for s in caveats)+'</ul>'
    body += '<table><tr><th>Metric</th>'+''.join('<th>'+esc(r['label'])+'</th>' for r in data)+'</tr>'
    body += ''.join('<tr><td>'+esc(label)+'</td>'+''.join(f'<td>{v:.4f}</td>' for v in values)+'</tr>' for label, values in metrics)+'</table>'
    body += '<p>Termination: '+esc(json.dumps(health))+'</p>'
    rng = random.Random(3407)
    chosen = [rng.choice([r for r in data[0]['rows'] if r['task']==task]) for task in dict.fromkeys(r['task'] for r in data[0]['rows'])]
    for row in chosen:
        target = row['target'] if isinstance(row['target'],str) else json.dumps(row['target'],ensure_ascii=False,indent=2)
        lines += ['='*70, row['id'], 'PROMPT:', row['semantic_prompt'], '', 'REFERENCE:', target, '']
        body += '<section><h2>'+esc(row['id'])+'</h2><details><summary>Full prompt</summary><pre>'+esc(row['semantic_prompt'])+'</pre></details><h3>Reference</h3><pre>'+esc(target)+'</pre><div class="answers">'
        for run in data:
            answer = next(r for r in run['rows'] if r['id']==row['id'])
            lines += [run['label']+' — FULL ANSWER:', answer['prediction'], 'Termination: '+answer['finish_reason'], '']
            body += '<article><h3>'+esc(run['label'])+'</h3><pre>'+esc(answer['prediction'])+'</pre><p>'+esc(answer['finish_reason'])+'</p></article>'
        body += '</div></section>'
    a.output_dir.mkdir(parents=True,exist_ok=True)
    stem = a.output_dir/'LFM3-CPT-PAIR-20261112'
    stem.with_suffix('.txt').write_text('\n'.join(lines),encoding='utf-8')
    stem.with_suffix('.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>LFM CPT pair</title><style>body{max-width:1500px;margin:30px auto;padding:20px;font:16px system-ui}table{border-collapse:collapse}td,th{padding:10px;border:1px solid #ccc}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.6 system-ui}.answers{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}article,section{padding:15px;border:1px solid #ddd;margin:20px 0}@media(max-width:950px){.answers{grid-template-columns:1fr}}</style>'+body+'</html>',encoding='utf-8')
    report = dict(status='completed_matched_pair_report',metrics=[dict(metric=k,values=v) for k,v in metrics],
        columns=[r['label'] for r in data],termination=health,selected_ids=[r['id'] for r in chosen],
        caveats=caveats,source_sha256=hashes)
    (a.model_root/'cpt-pair-results-v01.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(report=str(stem),metrics=report['metrics'],termination=health),indent=2))


if __name__ == '__main__':
    main()
