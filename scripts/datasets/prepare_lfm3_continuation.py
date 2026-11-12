"""Freeze a nested Wikipedia/FineWeb CPT pair; never sample FineWeb test.

Streaming uses a bounded, shuffled convenience frame, not a population sample.
Preserve full selected metadata and report that sampling limitation explicitly.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import random
import re
import statistics
import hashlib
import heapq
from urllib.parse import urlsplit

from prepare_lfm3_cpt import norm, sha, shingles, WEB_REV


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline-dir', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--target-tokens', type=int, default=10_000_000)
    p.add_argument('--scan-limit', type=int, default=400_000)
    p.add_argument('--parent-experiment', type=Path, required=True)
    a = p.parse_args()
    from datasets import load_dataset
    from transformers import AutoTokenizer
    base = a.baseline_dir
    if a.output_dir.exists():
        raise ValueError('Refusing to overwrite frozen output')
    cfg = json.loads((base/'config-planned.json').read_text())
    tokenizer = AutoTokenizer.from_pretrained(**dict(
        pretrained_model_name_or_path=cfg['model']['repo'], revision=cfg['model']['revision']))
    parent = json.loads((base/'cpt-data-manifest-v02.json').read_text())
    groups = {}
    for name, receipt in parent['splits'].items():
        blob = (base/'data-local/cpt-v02'/f'{name}.jsonl').read_bytes()
        if sha(blob) != receipt['sha256']:
            raise ValueError('Parent data checksum mismatch')
        groups[name] = [json.loads(s) for s in blob.decode().splitlines()]
    index, sizes, exact, paragraphs = defaultdict(set), [], set(), set()

    anchor_index, anchor_texts = defaultdict(set), []
    def anchors(words):
        return heapq.nsmallest(12,(int.from_bytes(hashlib.blake2b(w.encode(),digest_size=8).digest(),'little') for w in words))
    def add(text, protected=True):
        words = shingles(text)
        if protected:
            number = len(sizes)
            sizes.append(len(words))
            for word in words:
                index[word].add(number)
        aid = len(anchor_texts)
        anchor_texts.append(text)
        for key in anchors(words): anchor_index[key].add(aid)
        exact.add(sha(norm(text).encode()))
        paragraphs.update(sha(norm(s).encode()) for s in text.split('\n') if len(norm(s)) >= 200)

    for rows in groups.values():
        for row in rows:
            add(row['text'])
    for filename, expected in [('questions-500.jsonl',parent['benchmark_sha256']),
                               ('turblimp-1600.jsonl',parent['turblimp_sha256'])]:
        blob = (base/'data-local'/filename).read_bytes()
        if sha(blob) != expected:
            raise ValueError('Protected benchmark checksum mismatch')
        for line in blob.decode().splitlines():
            row = json.loads(line)
            if 'sentence_good' in row:
                add(row['sentence_good']); add(row['sentence_bad'])
            else:
                add(row['semantic_prompt'])
                doc = row['document']
                for key in ('text','context','source','target','summary'):
                    if isinstance(doc.get(key),str): add(doc[key])
                for text in doc.get('translation',{}).values(): add(text)
    previous_config=json.loads((a.parent_experiment/'config-planned.json').read_text())
    previous_manifest=json.loads((a.parent_experiment/previous_config['active_cpt_manifest']).read_text())
    previous_file=a.parent_experiment/previous_config['active_cpt_data']/'wiki_train.jsonl'
    assert sha(previous_file.read_bytes())==previous_manifest['splits']['wiki_train']['sha256']
    for line in previous_file.read_text(encoding='utf-8').splitlines(): add(json.loads(line)['text'],protected=False)
    excluded_ids=set(json.loads((base.parent/'cpt-pair-sample-review-v01.json').read_text())['excluded_ids'])
    wiki = groups['wiki_train']
    lengths = [len(ids) for ids in tokenizer([r['text'] for r in wiki],add_special_tokens=False)['input_ids']]
    wiki_tokens = sum(lengths)
    web, web_lengths, domains, dumps, counters = [], [], Counter(), Counter(), Counter()
    # Four pinned train shards, interleaved by the streaming reader and shuffled.
    files = [f'data/tur_Latn/train/000_{i:05}.parquet' for i in range(4)]
    stream = load_dataset('HuggingFaceFW/fineweb-2', name='tur_Latn', revision=WEB_REV,
        data_files={'train':files}, split='train', streaming=True)
    stream = stream.shuffle(seed=3407,buffer_size=10_000)
    web_budget = a.target_tokens-wiki_tokens
    if web_budget <= 0: raise ValueError('Target must exceed Wiki token count')
    for doc in stream:
        counters['scanned'] += 1
        if counters['scanned'] > a.scan_limit: break
        if 'fineweb-train-'+str(doc['id']) in excluded_ids:
            counters['prior_review_exclusion'] += 1; continue
        text = doc['text']; cleaned = norm(text)
        host = (urlsplit(doc.get('url','')).hostname or '').lower().removeprefix('www.')
        if host.endswith(('wikipedia.org','wikimedia.org','wikidata.org')):
            counters['wikimedia_host_excluded'] += 1; continue
        if host.endswith(('tripadvisor.com.tr','tripadvisor.com','agoda.com','booking.com','hotels.com')):
            counters['translated_hotel_template_excluded'] += 1; continue
        if any(term in host for term in ('fulloyun','cshile','filmpo','sifamarket','cinselsaglikurunleri','carmenajans','artconsept')) or re.search(r'rar\s*\u015fifresi\s*:|crack\s*:\s*mevcut|indirmek i\u00e7in t\u0131klay\u0131n|norecoil|setburst|bayan azd\u0131r\u0131c\u0131|antivir\u00fcs.*(?:kapat|devre d\u0131\u015f\u0131)|(?:720p|1080p).{0,35}(?:izle|indir)',cleaned.casefold()):
            counters['review_informed_spam_download_excluded']+=1;continue
        if any(term in cleaned.casefold() for term in ('gerçek para ile oyn','gerçek parayla oyn',
                'rar şifresi:', 'linkleri görebilmeniz için üye', 'linkeri görebilmeniz için üye',
                'sohbet hattı','bayan telefon numara','film yükleniyor','reklamı geçmek için')):
            counters['gambling_or_download_wall_excluded'] += 1; continue
        # Conservative commercial-spam screen, not a general safety classifier.
        commercial = re.findall(r'\b(?:eskort|escort|porno|porn|bahis|casino)\w*',cleaned.casefold())
        if len(commercial)>=2 or any(term in host for term in ('escort','eskort','porno','casino','bahis')):
            counters['commercial_spam_excluded'] += 1; continue
        if not 500 <= len(cleaned) <= 20000 or sum(c.isalpha() for c in cleaned)/len(cleaned) < .65:
            counters['length_or_letter_filter'] += 1; continue
        if doc.get('language') != 'tur' or float(doc.get('language_score',0)) < .9:
            counters['language_filter'] += 1; continue
        sentences = re.split(r'[.!?]+', cleaned)
        if len(re.findall(r'\w+',cleaned)) < 120 or sum(len(s.split())>=6 for s in sentences)<4:
            counters['insufficient_prose_excluded'] += 1; continue
        if len(re.findall(r'\b(?:rezervasyon|sipariş|indirimli|kampanya|kargoda)\w*',cleaned.casefold()))>=3:
            counters['commercial_template_excluded'] += 1; continue
        lines = [norm(s) for s in text.split('\n') if norm(s)]
        if len(lines)>=15 and sum(len(s.split())<6 for s in lines)/len(lines)>.6:
            counters['navigation_heavy_excluded'] += 1; continue
        if lines and 1-len(set(lines))/len(lines) > .2:
            counters['repeated_lines_filter'] += 1; continue
        digest = sha(cleaned.encode())
        paras = {sha(norm(s).encode()) for s in text.split('\n') if len(norm(s)) >= 200}
        if digest in exact or paras & paragraphs:
            counters['exact_or_paragraph_overlap'] += 1; continue
        words = shingles(text)
        hits = Counter(i for word in words for i in index.get(word,()))
        if any(count/min(len(words),sizes[i]) >= .8 for i,count in hits.items()):
            counters['near_overlap'] += 1; continue
        candidate_hits=Counter(i for key in anchors(words) for i in anchor_index.get(key,()))
        candidates=[i for i,n in candidate_hits.items() if n>=2]
        if len(candidates)>256:
            counters['common_template_anchor_excluded']+=1;continue
        if any(len(words & (other:=shingles(anchor_texts[i])))/min(len(words),len(other))>=.8 for i in candidates):
            counters['anchor_near_overlap']+=1;continue
        if not host:
            counters['missing_host'] += 1; continue
        length = len(tokenizer(text,add_special_tokens=False)['input_ids'])
        # Host cap bounds concentration, but does not merge sibling subdomains.
        if domains[host]+length > web_budget*.01:
            counters['host_cap'] += 1; continue
        record = dict(doc)
        record.update(id='fineweb-train-'+str(doc['id']), source_id=doc['id'],
            source='HuggingFaceFW/fineweb-2',source_revision=WEB_REV,source_split='train',
            normalized_text_sha256=digest,host=host,lfm_raw_tokens=length)
        web.append(record); web_lengths.append(length)
        domains[host] += length; dumps[str(doc.get('dump'))] += length
        add(text,protected=False)
        if len(web)%1000 == 0:
            print(json.dumps(dict(web_documents=len(web),web_tokens=sum(web_lengths),scanned=counters['scanned'])),flush=True)
        if sum(web_lengths) >= web_budget: break
    if sum(web_lengths) < web_budget:
        raise ValueError(f'Insufficient clean frame: {sum(web_lengths)} web tokens')
    a.output_dir.mkdir(parents=True)
    groups['wiki_train'] = wiki+web  # Compatibility name; explicitly mixed in manifest.
    random.Random(3407).shuffle(groups['wiki_train'])
    receipts = {}
    for name, rows in groups.items():
        blob = (''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows).encode()
                if name=='wiki_train' else (base/'data-local/cpt-v02'/f'{name}.jsonl').read_bytes())
        (a.output_dir/f'{name}.jsonl').write_bytes(blob)
        receipts[name] = dict(count=len(rows),sha256=sha(blob),ids=[r['id'] for r in rows])
    def stats(values):
        ordered = sorted(values)
        return dict(count=len(values),tokens=sum(values),mean=statistics.mean(values),
            std_population=statistics.pstdev(values),min=min(values),max=max(values),
            percentiles={str(q):ordered[round((len(ordered)-1)*q/100)] for q in (50,90,95,99)})
    report = dict(status='prepared_pending_manual_sample_review',model=cfg['model'],seed=3407,
        splits=receipts,source_files=files,web_revision=WEB_REV,source_split='train',
        parent_manifest_sha256=sha((base/'cpt-data-manifest-v02.json').read_bytes()),
        benchmark_sha256=parent['benchmark_sha256'],turblimp_sha256=parent['turblimp_sha256'],
        raw_tokens_no_eos=dict(wikipedia=stats(lengths),fineweb=stats(web_lengths),combined=stats(lengths+web_lengths)),
        web_host_tokens=dict(domains.most_common()),web_dump_tokens=dict(dumps),counters=dict(counters),
        policy='Same Wiki rows; shuffled combined order seed3407; train-only web, language_score>=.9, 500..20000 NFC chars, >=120 words and >=4 sentence spans with >=6 words each, letter ratio>=.65, repeated-line fraction<=.2, <=.6 short-line fraction for pages with >=15 lines; host<=1% web token budget; exclude Wikimedia hosts, known translated hotel template hosts, conservative adult/gambling commercial spam and download-wall indicators, >=3 commercial-template word matches; exact text, >=200-char paragraph and >=.8 five-word containment exclusions against all selected/protected text',
        limitations=['Bounded shuffled frame from four train shards; not representative of all FineWeb2',
            'Cross-train near-duplicate search uses 12 bottom-hash anchors (>=2 shared) then exact five-word containment; approximate candidate recall, not exhaustive. Benchmark/eval and original Wiki use exhaustive five-word inverted-index checks', 'Prior CPT-B exact/paragraph/anchor-near duplicates excluded; additional tokens are fresh FineWeb prose, not replayed Wiki', 'Host cap is not a registrable-domain cap', 'No native topic labels; no claim of equal topic balance',
            'Heuristic prose filtering biases against lists, short pages and some legitimate commerce; factual accuracy not certified',
            'No guarantee of semantic or base-pretraining independence',
            'Web evaluation is now same-source held-out; historical cohort previously inspected',
            'Whole-document budget may slightly exceed 10M; trainer EOS/packing exposure measured separately'])
    (a.output_dir/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    sample = random.Random(3407).sample(web,min(30,len(web)))
    (a.output_dir/'review-sample.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in sample),encoding='utf-8')
    print(json.dumps(report['raw_tokens_no_eos']),flush=True)


if __name__ == '__main__':
    main()
