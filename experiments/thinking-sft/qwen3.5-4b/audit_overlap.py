"""Compare authored prompts against available historical Turkish/Occam JSONL.

This is a bounded lexical audit, not a semantic-independence guarantee.
"""
import argparse
import collections
import difflib
import json
from pathlib import Path

from pipeline import ROOT, DATA, normalize, read_rows, sha, write_json


def user_text(row):
    messages = row.get('messages', row.get('conversations', []))
    if isinstance(messages, list):
        parts = [m.get('content', m.get('value', '')) for m in messages if isinstance(m, dict)
                 and m.get('role', m.get('from')) in ('user', 'human')]
        if parts and all(isinstance(x, str) for x in parts):
            return '\n'.join(parts)
    for key in ('prompt', 'question', 'instruction', 'input'):
        if isinstance(row.get(key), str) and row[key].strip():
            return row[key]
    return ''


def grams(text):
    words = text.split()
    return {' '.join(words[i:i+3]) for i in range(len(words)-2)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    repo = ROOT.parents[2]
    files = sorted(set(path for base in [repo/'experiments/response-style-control', repo/'experiments/turkish-capability']
        for path in base.rglob('*.jsonl') if 'data' in str(path.parent) and any(k in path.name for k in ('train', 'validation', 'question'))))
    history, sources, skipped = [], {}, []
    for path in files:
        count = 0
        with path.open() as stream:
            for index, line in enumerate(stream):
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    skipped.append(str(path.relative_to(repo)))
                    break
                if isinstance(row, dict):
                    prompt = normalize(user_text(row))
                    if prompt:
                        history.append((prompt, str(path.relative_to(repo)), index+1))
                        count += 1
        sources[str(path.relative_to(repo))] = dict(rows=count, sha256=sha(path))
    inverted = collections.defaultdict(set)
    exact = collections.defaultdict(list)
    for index, (text, _, _) in enumerate(history):
        exact[text].append(index)
        for gram in grams(text):
            inverted[gram].add(index)
    flags = []
    for name in ('train.jsonl', 'test-prompts.jsonl'):
        for row in read_rows(DATA/name):
            text = normalize(user_text(row))
            shared = collections.Counter(index for gram in grams(text) for index in inverted.get(gram, ()))
            candidates = set(exact.get(text, [])) | {i for i, _ in shared.most_common(10)}
            for index in candidates:
                old, source, line = history[index]
                ratio = difflib.SequenceMatcher(None, text, old).ratio()
                if text == old or ratio >= .65:
                    flags.append(dict(id=row['id'], source=source, line=line,
                                      exact=text == old, similarity=round(ratio, 3)))
    write_json(args.output, dict(method='Normalized exact match plus top10 trigram candidates, sequence similarity >=0.65',
        historical_rows=len(history), historical_files=len(files), flags=flags, skipped=skipped,
        sources=sources, limitation='Only local available JSONL and supported prompt fields inspected; no semantic or contamination-free claim.'))
    print(json.dumps(dict(historical_rows=len(history), historical_files=len(files), flags=len(flags), skipped=len(skipped))))


if __name__ == '__main__':
    main()
