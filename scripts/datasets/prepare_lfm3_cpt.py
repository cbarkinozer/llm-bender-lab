"""Pinned, deterministic Turkish CPT pilot; benchmark text is evaluation only."""
import argparse
from collections import Counter, defaultdict
import hashlib
import heapq
import json
from pathlib import Path
import re
import unicodedata
import urllib.request

WIKI_REV = 'b04c8d1ceb2f5cd4588862100d08de323dccfbaa'
WEB_REV = 'af9c13333eb981300149d5ca60a8e9d659b276b9'


def norm(text):
    return ' '.join(unicodedata.normalize('NFC', text).split())


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def shingles(text):
    words = re.findall(r'\w+', norm(text).casefold())
    return {' '.join(words[i:i+5]) for i in range(len(words)-4)}


def download(repo, revision, file, cache):
    destination = cache / repo.replace('/', '--') / revision / file
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        partial = destination.with_suffix('.partial')
        url = f'https://huggingface.co/datasets/{repo}/resolve/{revision}/{file}'
        with urllib.request.urlopen(url, timeout=120) as source, partial.open('wb') as target:
            while chunk := source.read(1024 * 1024):
                target.write(chunk)
        partial.replace(destination)
    digest = hashlib.sha256()
    with destination.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return destination, dict(repo=repo, revision=revision, file=file,
        bytes=destination.stat().st_size, sha256=digest.hexdigest())


def records(path):
    import pyarrow.parquet as pq
    for batch in pq.ParquetFile(path).iter_batches(batch_size=512):
        yield from batch.to_pylist()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--experiment-dir', type=Path, required=True)
    parser.add_argument('--cache-root', type=Path, required=True)
    args = parser.parse_args()
    packet = args.experiment_dir / 'data-local/questions-500.jsonl'
    benchmark = [json.loads(line) for line in packet.read_text(encoding='utf-8').splitlines()]
    inverted = defaultdict(set)
    protected = []
    for row in benchmark:
        doc = row['document']
        texts = [row['semantic_prompt']]
        texts += [doc[k] for k in ('text', 'context', 'source', 'target', 'summary') if isinstance(doc.get(k), str)]
        if isinstance(doc.get('translation'), dict):
            texts += list(doc['translation'].values())
        for text in texts:
            words = shingles(text)
            if words:
                number = len(protected)
                protected.append(words)
                for word in words:
                    inverted[word].add(number)
    turblimp = args.experiment_dir / 'data-local/turblimp-1600.jsonl'
    if not turblimp.exists():
        raise ValueError('Prepare TurBLiMP first so it is excluded from training selection')
    for line in turblimp.read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        for text in (row['sentence_good'], row['sentence_bad']):
            words = shingles(text)
            if words:
                number = len(protected)
                protected.append(words)
                for word in words:
                    inverted[word].add(number)
    def overlaps(words):
        hits = Counter(i for word in words for i in inverted.get(word, ()))
        return any(count / min(len(words), len(protected[i])) >= .8 for i, count in hits.items()) if words else False
    counts = Counter()
    sources = []
    heap = []
    for index in range(2):
        file = f'20231101.tr/train-{index:05}-of-00002.parquet'
        path, evidence = download('wikimedia/wikipedia', WIKI_REV, file, args.cache_root)
        sources.append(evidence)
        print(f'Wiki shard {index}: downloaded/hashed', flush=True)
        for doc in records(path):
            counts['wiki_scanned'] += 1
            text = doc['text']
            cleaned = norm(text)
            if not 500 <= len(cleaned) <= 20000:
                counts['length_excluded'] += 1
                continue
            if sum(c.isalpha() for c in cleaned) / len(cleaned) < .65:
                counts['low_letter_ratio_excluded'] += 1
                continue
            if overlaps(shingles(cleaned)):
                counts['benchmark_overlap_excluded'] += 1
                continue
            rank = int(sha(('lfm3-cpt-v1-3407:' + str(doc['id'])).encode()), 16)
            record = dict(id='wiki-' + str(doc['id']), title=doc['title'], url=doc['url'], text=text,
                source='wikimedia/wikipedia', source_revision=WIKI_REV,
                normalized_text_sha256=sha(cleaned.encode()))
            entry = (-rank, record['id'], record)
            if len(heap) < 5000:
                heapq.heappush(heap, entry)
            elif entry[:2] > heap[0][:2]:
                heapq.heapreplace(heap, entry)
    chosen = []
    seen = set()
    paragraphs = set()
    selected_shingles = defaultdict(set)
    selected_sizes = []
    for _, _, doc in sorted(heap, key=lambda r: (-r[0], r[1])):
        paragraph_hashes = {sha(norm(p).encode()) for p in doc['text'].split('\n') if len(norm(p)) >= 200}
        words = shingles(doc['text'])
        hits = Counter(i for word in words for i in selected_shingles.get(word, ()))
        near = any(count / min(len(words), selected_sizes[i]) >= .8 for i, count in hits.items()) if words else False
        if doc['normalized_text_sha256'] in seen or paragraph_hashes & paragraphs or near:
            counts['selected_pool_duplicate_excluded'] += 1
            continue
        seen.add(doc['normalized_text_sha256'])
        paragraphs.update(paragraph_hashes)
        number = len(chosen)
        selected_sizes.append(len(words))
        for word in words:
            selected_shingles[word].add(number)
        chosen.append(doc)
        if len(chosen) == 3200:
            break
    if len(chosen) != 3200:
        raise ValueError(f'Insufficient clean pool: {len(chosen)}')
    groups = dict(wiki_eval=chosen[:100], wiki_dev=chosen[100:200], wiki_train=chosen[200:])
    path, evidence = download('HuggingFaceFW/fineweb-2', WEB_REV, 'data/tur_Latn/test/000_00000.parquet', args.cache_root)
    sources.append(evidence)
    web = []
    for number, doc in enumerate(records(path)):
        text = doc['text']
        cleaned = norm(text)
        if not 500 <= len(cleaned) <= 20000 or overlaps(shingles(cleaned)):
            continue
        words = shingles(cleaned)
        hits = Counter(i for word in words for i in selected_shingles.get(word, ()))
        if any(count / min(len(words), selected_sizes[i]) >= .8 for i, count in hits.items()):
            counts['web_wiki_overlap_excluded'] += 1
            continue
        digest = sha(cleaned.encode())
        paragraph_hashes = {sha(norm(p).encode()) for p in text.split('\n') if len(norm(p)) >= 200}
        if digest in seen or paragraph_hashes & paragraphs:
            continue
        seen.add(digest)
        paragraphs.update(paragraph_hashes)
        # Add web documents too so subsequent pages get the same near-duplicate check.
        idx = len(selected_sizes)
        selected_sizes.append(len(words))
        for word in words:
            selected_shingles[word].add(idx)
        web.append(dict(id=f'fineweb-test-{number}', text=text, url=doc.get('url'),
            source='HuggingFaceFW/fineweb-2', source_revision=WEB_REV,
            normalized_text_sha256=digest))
        if len(web) == 100:
            break
    if len(web) != 100:
        raise ValueError('Insufficient independent FineWeb pages')
    groups['web_eval'] = web
    output = args.experiment_dir / 'data-local/cpt-v02'
    output.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, rows in groups.items():
        blob = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows).encode()
        file = output / (name + '.jsonl')
        if file.exists() and file.read_bytes() != blob:
            raise ValueError('Refusing to overwrite different frozen data')
        file.write_bytes(blob)
        files[name] = dict(count=len(rows), sha256=sha(blob), ids=[r['id'] for r in rows])
    report = dict(status='prepared_cpu_not_semantically_certified', seed=3407,
        turblimp_sha256=sha(turblimp.read_bytes()),
        source_files=sources, benchmark_sha256=sha(packet.read_bytes()), counters=dict(counts), splits=files,
        selection='Wikipedia stable SHA256 ID rank; FineWeb first eligible pages from pinned test shard',
        policy='500..20000 normalized characters, letter ratio>=.65 for Wikipedia; NFC whitespace normalized; exact document and >=200-character paragraph dedup; casefolded five-word containment>=.8 against CETVEL and selected documents',
        limitations=['No guarantee of pretraining independence', 'Not a semantic/domain balance audit',
            'Five-word overlap cannot detect all semantic paraphrases or sentences shorter than five words', 'Wikipedia text loss and benchmark task metrics are separate outcomes',
            'FineWeb evaluation is a deterministic prefix convenience sample, not a population estimate'])
    (args.experiment_dir / 'cpt-data-manifest-v02.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({name: len(rows) for name, rows in groups.items()}), flush=True)


if __name__ == '__main__':
    main()
