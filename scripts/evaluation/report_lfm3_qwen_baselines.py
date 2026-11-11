"""Historical aggregate comparison and seeded examples; never invent missing outputs."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import random


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--qwen-answers',type=Path)
    a=p.parse_args()
    root=Path(__file__).resolve().parents[2]
    exp=root/'experiments/turkish-capability/lfm3-1.7b/exp-000-baseline'
    lbase=exp/'results-local/base-v01'
    qbase=root/'experiments/turkish-capability/qwen3.5-4b/exp-003-cetvel-500/results-v1'
    load=lambda file:json.loads(file.read_text(encoding='utf-8'))
    lm=load(lbase/'cetvel/manifest.json');qm=load(qbase/'base/manifest.json')
    assert lm['status']==qm['status']=='completed'
    assert lm['questions_sha256']==qm['questions_sha256'] and lm['count']==qm['count']==500
    l=load(lbase/'cetvel/scores.json')['results'];q=load(qbase/'comparison.json')['results']['base']
    specs=[('GECTurk exact correction','gecturk','exact_match_rate',100),
        ('TQUAD F1','tquad','f1',100),('XQuAD-TR F1','xquad_tr','f1',100),
        ('EN→TR BLEU','wmt_en_tr','corpus_bleu',1),('EN→TR chrF','wmt_en_tr','corpus_chrf',1),
        ('MLSum ROUGE-L','mlsum_tr','mean_rougeL',100)]
    metrics=[dict(metric=name,qwen=q[task][key]*scale,lfm=l[task][key]*scale)
        for name,task,key,scale in specs]
    rows=[json.loads(s) for s in (lbase/'cetvel/answers.jsonl').read_text(encoding='utf-8').splitlines()]
    rng=random.Random(3407)
    selected=[rng.choice([r for r in rows if r['task']==task]) for task in dict.fromkeys(r['task'] for r in rows)]
    qrows={}
    if a.qwen_answers:
        qrows={r['id']:r for r in map(json.loads,a.qwen_answers.read_text(encoding='utf-8').splitlines())}
        assert len(qrows)==500
        for row in rows:
            assert row['id'] in qrows
            other=qrows[row['id']]
            assert row['semantic_prompt']==other['semantic_prompt'] and row['document_sha256']==other['document_sha256']
    caveats=['Aynı sabit500 soru; görev başına100. Qwen base, SFT/Occam/F adaptörü değil.',
        'İki model de BF16, thinking kapalı, greedy, repetition penalty1.05,4096 çıktı/8192 bağlam.',
        'Qwen4B, LFM1.7B; vLLM sürümleri, tokenizer/chat şablonları farklı. Qwen batch8, LFM sequential1; süreleri hız yarışı olarak yorumlamayın.',
        'QA F1/ROUGE/GEC tam eşleşme, gereksiz açıklamalardan etkilenir; insan doğruluğu ile aynı şey değildir.',
        'Qwen ham yanıtları bu makinede bulunamadı. Skor karşılaştırması geçerli; birebir yanıt karşılaştırması için eski yedek gerekir.' if not qrows else 'Qwen ham yanıtları kimlik/prompt/kaynak hash ile eşleştirildi.',
        'Rastgele seçim: Python Random(3407), görev başına1; sonuç kalitesine göre örnek seçilmedi. Tüm prompt ve yanıtlar kısaltılmadan verilmiştir.']
    lines=['LFM3-1.7B / Qwen3.5-4B BASELINE KARŞILAŞTIRMASI','',*caveats,'',
        'Metrik | Qwen3.5-4B base | LFM3-1.7B base']
    lines += [f"{m['metric']} | {m['qwen']:.2f} | {m['lfm']:.2f}" for m in metrics]
    grammar=load(lbase/'turblimp/scores.json')['macro_accuracy']*100
    text_scores=load(lbase/'text/text-scores.json')['results']
    ppl={key:row['perplexity'] for key,row in text_scores.items()}
    lines += ['',f'LFM TurBLiMP1600: %{grammar:.2f}. Eşleşmiş Qwen ölçümü yok.',
        f"LFM Wikipedia perplexity: {ppl['wiki_eval']:.2f}; FineWeb perplexity: {ppl['web_eval']:.2f}. Tokenizer farklı modellerin perplexity değerleri doğrudan kıyaslanmaz.",
        'LFM:496 EOS/4 length;500 çıktının tamamı puanlandı. CPT yapılmadı.',
        'Qwen base:496 EOS/4 repetition guard;500 çıktının tamamı puanlandı.','']
    examples=[]
    for row in selected:
        other=qrows.get(row['id'])
        qp=other.get('prediction',other.get('raw_output','')) if other else 'HAM QWEN YANITI BU MAKİNEDE YOK — yeniden üretilmedi/uydurulmadı.'
        target=json.dumps(row['target'],ensure_ascii=False,indent=2) if not isinstance(row['target'],str) else row['target']
        item=dict(id=row['id'],task=row['task'],prompt=row['semantic_prompt'],reference=target,
            lfm=row['prediction'],qwen=qp)
        examples.append(item)
        lines += ['='*70,row['id'],'PROMPT:',item['prompt'],'','REFERANS:',target,'',
            'LFM3-1.7B (TAM YANIT):',item['lfm'],'','QWEN3.5-4B:',qp,'']
    a.output_dir.mkdir(parents=True,exist_ok=True)
    stem=a.output_dir/'LFM3-QWEN-BASELINE-20261111'
    stem.with_suffix('.txt').write_text('\n'.join(lines),encoding='utf-8')
    esc=html.escape
    body='<h1>LFM3 / Qwen — temel model karşılaştırması</h1>'
    body+='<ul>'+''.join('<li>'+esc(s)+'</li>' for s in caveats)+'</ul>'
    body+='<table><tr><th>Metrik</th><th>Qwen4B base</th><th>LFM1.7B base</th></tr>'
    body+=''.join(f"<tr><td>{esc(m['metric'])}</td><td>{m['qwen']:.2f}</td><td>{m['lfm']:.2f}</td></tr>" for m in metrics)+'</table>'
    body+=f'<p>LFM TurBLiMP: %{grammar:.2f}. Qwen ölçümü yok. LFM496EOS/4length; CPT yapılmadı.</p>'
    body+=f"<p>LFM perplexity: Wikipedia {ppl['wiki_eval']:.2f}, FineWeb {ppl['web_eval']:.2f}. Bunlar CPT sonrası aynı tokenizer ile kıyaslanacak; Qwen ile doğrudan kıyas değil.</p>"
    for row in examples:
        body+=f"<section><h2>{esc(row['id'])}</h2><details><summary>Tam prompt / kaynak metin</summary><pre>{esc(row['prompt'])}</pre></details><h3>Referans</h3><pre>{esc(row['reference'])}</pre><div class='pair'><article><h3>LFM3 — tam yanıt</h3><pre>{esc(row['lfm'])}</pre></article><article><h3>Qwen — tam yanıt</h3><pre>{esc(row['qwen'])}</pre></article></div></section>"
    stem.with_suffix('.html').write_text('<!doctype html><html lang="tr"><meta charset="utf-8"><title>LFM3 / Qwen</title><style>body{max-width:1300px;margin:30px auto;font:16px system-ui;padding:20px;background:#fafafa;color:#202020}table{border-collapse:collapse}td,th{padding:10px;border:1px solid #ccc}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.6 system-ui}.pair{display:grid;grid-template-columns:1fr 1fr;gap:24px}article,section{padding:18px;border:1px solid #ddd;background:white;margin:20px 0}li{margin:10px 0}@media(max-width:750px){.pair{grid-template-columns:1fr}}</style>'+body+'</html>',encoding='utf-8')
    summary=dict(status='aggregate_comparison_complete_paired_raw_qwen_unavailable' if not qrows else 'paired_comparison_available',
        questions_sha256=lm['questions_sha256'],metrics=metrics,seed=3407,selected_ids=[r['id'] for r in selected],
        qwen_raw_available=bool(qrows),caveats=caveats,lfm_turblimp=grammar,
        source_sha256={str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in (lbase/'cetvel/scores.json',qbase/'comparison.json')})
    (exp/'baseline-qwen-comparison-v01.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(dict(report=str(stem),selected_ids=summary['selected_ids'],qwen_raw_available=bool(qrows))))


if __name__=='__main__':main()
