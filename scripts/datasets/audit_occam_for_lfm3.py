"""Read-only Occam inspection for a new LFM3 SFT mixture; no target generation."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import unicodedata


def normalized(s):
    return ' '.join(unicodedata.normalize('NFC', s).casefold().split())


def main():
    from huggingface_hub import hf_hub_download
    from tokenizers import Tokenizer
    root = Path(__file__).resolve().parents[2]
    track = root/'experiments/turkish-capability/lfm3-1.7b'
    output = track/'sft-expansion-v01'
    output.mkdir(exist_ok=True)
    revision = '947850d484c71f657dbec2bb7e3d356cb5fb23e3'
    source = root/'experiments/response-style-control/qwen3.5-4b/exp-016-diverse-coverage-sft/data-reviewed-v1'
    tokenizer_path = track/'exp-004-cpt-cont-100m/results-local/cpt-v01/adapter/tokenizer.json'
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    def digest(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()
    def stats(values):
        return dict(count=len(values), mean=statistics.mean(values),
            std_population=statistics.pstdev(values), min=min(values), max=max(values))
    inventory = dict(source_repo='cbarkinozer/Occam-Turkish-Response-SFT',revision=revision,
        declared_license='apache-2.0', historical_provenance_review='incomplete; see original dataset card',
        tokenizer_repo='LiquidAI/LFM3-1.7B',tokenizer_revision='0dc4268b561499c648c7ba7c9466bf3d8d01517a',
        tokenizer_sha256=digest(tokenizer_path),
        token_count_scope='Raw concatenated input content and target separately, add_special_tokens=False; not serialized training/masked-loss exposure.',
        splits={}, limitations=['Static inspection only, no new human target adjudication.',
            'Exact overlap checks do not establish absence of semantic near-duplicates or pretraining contamination.',
            'Published license declaration is not proof that all historical provider terms were reviewed.'])
    split_rows = {}
    for split, filename in [('train','train-reviewed.jsonl'),('validation','validation-reviewed.jsonl')]:
        rows = [json.loads(s) for s in (source/filename).read_text(encoding='utf-8').splitlines()]
        public = Path(hf_hub_download(inventory['source_repo'],'data/'+split+'.jsonl',repo_type='dataset',revision=revision))
        published = [json.loads(s) for s in public.read_text(encoding='utf-8').splitlines()]
        assert len(rows) == len(published)
        for a,b in zip(rows,published):
            assert b['messages'][-1]['role'] == 'assistant'
            assert a['messages'] == b['messages'][:-1] and a['desired_answer'] == b['messages'][-1]['content'], a['id']
        assert len({r['id'] for r in rows}) == len(rows)
        prompts = ['\n'.join(m['content'] for m in r['messages']) for r in rows]
        answers = [r['desired_answer'] for r in rows]
        assert all(answers) and all(prompts)
        split_rows[split] = rows
        summary = [r for r in rows if r['category'] == 'faithful_summary']
        inventory['splits'][split] = dict(rows=len(rows),local_sha256=digest(source/filename),
            published_file_sha256=digest(public),published_prompt_target_identity='all rows exact and same order',
            categories=dict(Counter(r['category'] for r in rows)),
            origins=dict(Counter(r.get('origin','missing') for r in rows)),
            provenance_review_states=dict(Counter(r.get('answer_status','missing') for r in rows)),
            raw_input_tokens=stats([len(tokenizer.encode(p,add_special_tokens=False).ids) for p in prompts]),
            raw_answer_tokens=stats([len(tokenizer.encode(p,add_special_tokens=False).ids) for p in answers]),
            replacement_characters=sum(s.count('\ufffd') for s in prompts+answers),
            duplicate_normalized_prompts=len(prompts)-len({normalized(s) for s in prompts}),
            summary_ids=[r['id'] for r in summary],
            summary_answer_characters=stats([len(r['desired_answer']) for r in summary]))
    left = split_rows['train']; right = split_rows['validation']
    prompt_set = lambda rows:{normalized('\n'.join(m['content'] for m in r['messages'])) for r in rows}
    group_set = lambda rows:{r['scenario_group_id'] for r in rows if r.get('scenario_group_id')}
    inventory['train_validation_exact_prompt_overlap'] = len(prompt_set(left)&prompt_set(right))
    inventory['train_validation_scenario_group_overlap'] = sorted(group_set(left)&group_set(right))
    cohort = track/'exp-000-baseline/data-local/questions-500.jsonl'
    benchmark = [json.loads(s) for s in cohort.read_text(encoding='utf-8').splitlines()]
    protected = prompt_set(benchmark)
    inventory['cetvel500_questions_sha256'] = digest(cohort)
    inventory['exact_prompt_matches_to_cetvel500'] = {split:len(prompt_set(rows)&protected) for split,rows in split_rows.items()}
    inventory['training_readiness'] = 'not_ready: semantic overlap review, historical provenance disposition, target review and LFM native loss-mask/token audits still required'
    (output/'occam-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(inventory,ensure_ascii=True,indent=2))


if __name__ == '__main__':
    main()
