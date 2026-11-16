"""Freeze submitted Argilla reviews, apply owner edits, and describe the reviewed pilot.

Reads Argilla only on first export; subsequent runs use the committed snapshot.
Does not mutate Argilla, normalize owner prose, serialize a chat template, or train.
"""
import collections
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import statistics

from tokenizers import Tokenizer
from audit_turkish_sources import ROOT, OUT, filehash, norm

DEST = ROOT / 'experiments/turkish-capability/lfm3-1.7b/reviewed-pilot-v01'
NAMES = {'train': 'turkish-sft-source-calibration-v01', 'test': 'turkish-sft-holdout-test-v01'}
TOKENIZER_HASH = '7e226e34bface23ccf6e495d157bf77186c1c30a7659880e1a8994db528c3701'


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def lines(path, rows):
    path.write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in rows), encoding='utf-8', newline='\n')


def stats(values):
    v = sorted(values)
    return dict(n=len(v), total=sum(v), min=min(v), median=statistics.median(v),
                mean=round(statistics.mean(v), 2), p90=v[int((len(v)-1)*.9)],
                p95=v[int((len(v)-1)*.95)], max=max(v))


def separate(text):
    # Both observed thinking spelling and source think spelling map to semantic fields.
    match = re.fullmatch(r'\s*<(think|thinking)>(.*?)</\1>\s*(.+?)\s*', text, flags=re.S)
    if match:
        return match.group(2).strip(), match.group(3).strip()
    if re.search(r'</?(?:think|thinking)>', text):
        raise ValueError('Malformed or non-leading reasoning tags')
    return None, text


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    snapshot_path = DEST / 'argilla-submitted-snapshot.json'
    if snapshot_path.exists():
        snapshot = json.loads(snapshot_path.read_text(encoding='utf-8'))
    else:
        import argilla as rg
        import os
        env = ROOT / 'experiments/response-style-control/qwen3.5-4b/exp-001-sft-dataset/annotation/argilla/.env'
        if env.exists():
            for line in env.read_text(encoding='utf-8-sig').splitlines():
                key, sep, value = line.partition('=')
                if sep and key.strip() in ['ARGILLA_API_KEY', 'ARGILLA_WORKSPACE']:
                    os.environ.setdefault(key.strip(), value.strip().strip('\"').strip("'"))
        client = rg.Argilla(api_url='http://127.0.0.1:6900', api_key=os.getenv('ARGILLA_API_KEY', 'argilla.apikey'))
        snapshot = dict(exported_at_utc=datetime.now(timezone.utc).isoformat(), datasets={})
        for split, name in NAMES.items():
            ds = client.datasets(name=name, workspace=os.getenv('ARGILLA_WORKSPACE', 'sft-review'))
            records = list(ds.records)
            assert len(records) == (80 if split == 'train' else 20)
            assert all(str(r.status) == 'completed' for r in records), 'Unsubmitted review exists'
            snapshot['datasets'][split] = dict(name=name, id=str(ds.id), guidelines=ds.settings.guidelines,
                records=[dict(r.to_dict(), response_statuses=[dict(question=x.question_name,
                    user_id=str(x.user_id), status=str(x.status)) for x in r.responses]) for r in records])
        dump(snapshot_path, snapshot)

    dump(snapshot_path, snapshot)  # Stable LF bytes across Windows/Linux checkouts.
    tokpath = OUT / 'raw-local/tokenizer/tokenizer.json'
    assert filehash(tokpath) == TOKENIZER_HASH
    tokenizer = Tokenizer.from_file(str(tokpath))
    count = lambda text: len(tokenizer.encode(text, add_special_tokens=False).ids)
    allrows = []; measures = []; excluded = []
    for split, ds in snapshot['datasets'].items():
        packet_path = OUT / f'review-local/review-100-{split}.jsonl'
        packet = {r['id']: r for r in map(json.loads, packet_path.read_text(encoding='utf-8').splitlines())}
        assert set(packet) == {r['id'] for r in ds['records']}
        for raw in ds['records']:
            assert raw['status']=='completed'
            assert all(x['status'].split('.')[-1]=='submitted' for x in raw['response_statuses'])
            p = packet[raw['id']]; responses = raw['responses']
            def value(key):
                entries = responses.get(key, [])
                assert len(entries) <= 1, 'Multiple reviewers require adjudication'
                return entries[0]['value'] if entries else None
            decision = value('decision')
            if decision not in ['keep', 'edit']:
                excluded.append(dict(id=p['id'], split=split, decision=decision)); continue
            assert value('correctness') == 'pass' and value('instruction') == 'pass', p['id']
            ms = [dict(m) for m in p['original_messages']]
            original_target = ms[-1]['content']; assert ms[-1]['role'] == 'assistant'
            original_users = [i for i,m in enumerate(ms) if m['role']=='user']
            corrected_user = value('corrected_user')
            if corrected_user:
                # Edits address the current user turn, preserving earlier dialogue context.
                ms[original_users[-1]]['content'] = corrected_user
            target = value('corrected_answer') if decision == 'edit' else original_target
            assert isinstance(target, str) and target.strip(), p['id']
            reasoning, final = separate(target)
            ms[-1]['content'] = final
            row = dict(id=p['id'], split=split, source_key=p['id'].split(':')[0],
                source={k:p.get(k) for k in ['source_repo','source_revision','source_filename','source_line_1based',
                    'source_row_id','source_category','source_split','original_record_sha256','source_prompt_sha256','source_answer_sha256']},
                messages=ms, worked_solution=reasoning, reviewed_target=target,
                review=dict(decision=decision, ratings={k:value(k) for k in ['correctness','instruction','turkish','detail']},
                    notes=value('notes'), prompt_edited=bool(corrected_user),
                    approval_basis='prior-owner-approval' if 'Applied from explicit owner instruction:' in (value('notes') or '') else 'individual-owner-review'),
                supervision=dict(assistant_turns='final-only', worked_solution_separate=reasoning is not None),
                intended_use='held-out-test-only' if split=='test' else 'training-candidate',
                release_status='owner-content-reviewed; native-template, source-lineage and semantic-leakage checks remain')
            # Preserve exact edits: separate semantic fields must reconstruct the target content.
            assert row['reviewed_target'] == target
            if decision=='edit': assert target == value('corrected_answer')
            assert '\ufffd' not in json.dumps(row, ensure_ascii=False)
            allrows.append(row)
            prompt = '\n'.join(m['content'] for m in ms if m['role']=='user')
            context = '\n'.join(m['content'] for m in ms[:-1] if m['role']!='system')
            system = '\n'.join(m['content'] for m in ms if m['role']=='system')
            original_reasoning, original_final = separate(original_target)
            measures.append(dict(id=p['id'], split=split, source=row['source_key'], category=p.get('source_category'),
                decision=decision, prompt_edited=bool(corrected_user), reasoning=reasoning is not None,
                turns=len(original_users), prompt_tokens=count(prompt), context_tokens=count(context), system_tokens=count(system),
                final_tokens=count(final), reasoning_tokens=count(reasoning or ''), target_tokens=count(final)+count(reasoning or ''),
                original_target_tokens=count(original_final)+count(original_reasoning or ''),
                final_words=len(final.split()), final_characters=len(final),
                markdown_heading=bool(re.search(r'^#{1,6}\s',final,re.M)),
                list_format=bool(re.search(r'^\s*(?:[-*]|\d+[.)])\s',final,re.M)),
                code_fence='```' in final, json_object=final.lstrip().startswith(('{','[')),
                table=bool(re.search(r'^\|.*\|\s*$',final,re.M)),
                question_in_answer='?' in final,
                normalized_prompt=norm(prompt), normalized_answer=norm(final)))
    assert len({r['id'] for r in allrows})==len(allrows)
    capabilities = json.loads((DEST/'capability-audit.json').read_text(encoding='utf-8'))
    dump(DEST/'capability-audit.json', capabilities)
    labels = {r['id']:r['primary_capability'] for r in capabilities['rows']}
    assert set(labels) == {r['id'] for r in allrows}
    for row in allrows:
        row['primary_capability'] = labels[row['id']]
        row['capability_label_basis'] = 'agent-descriptive; not owner-adjudicated'
    for m in measures:
        m['primary_capability'] = labels[m['id']]
    for split in NAMES:
        lines(DEST/f'{split}.jsonl', sorted([r for r in allrows if r['split']==split],key=lambda r:r['id']))
    lines(DEST/'excluded.jsonl',excluded)
    groups={}
    for split in NAMES:
        for source in ['all','occam','sft','atlas','cot']:
            rows=[m for m in measures if m['split']==split and (source=='all' or m['source']==source)]
            if not rows:continue
            groups[f'{split}/{source}']=dict(rows=len(rows),
                lengths={k:stats([r[k] for r in rows]) for k in ['prompt_tokens','context_tokens','system_tokens','final_tokens','reasoning_tokens','target_tokens','original_target_tokens','final_words','final_characters']},
                decisions=dict(collections.Counter(r['decision'] for r in rows)),
                prompt_edits=sum(r['prompt_edited'] for r in rows), reasoning_rows=sum(r['reasoning'] for r in rows),
                multi_turn_rows=sum(r['turns']>1 for r in rows),
                final_length_bins=dict(collections.Counter('0-64' if r['final_tokens']<=64 else '65-256' if r['final_tokens']<=256 else '257-512' if r['final_tokens']<=512 else '513+' for r in rows)),
                format_indicators={k:sum(r[k] for r in rows) for k in ['markdown_heading','list_format','code_fence','json_object','table','question_in_answer']},
                source_categories=dict(collections.Counter(str(r['category']) for r in rows)),
                primary_capabilities=dict(collections.Counter(r['primary_capability'] for r in rows)),
                above_raw_4096=sum(r['context_tokens']+r['system_tokens']+r['target_tokens']>4096 for r in rows),
                above_raw_8192=sum(r['context_tokens']+r['system_tokens']+r['target_tokens']>8192 for r in rows))
    duplicate_prompts=[]; duplicate_answers=[]; near=[]
    for key, dest in [('normalized_prompt',duplicate_prompts),('normalized_answer',duplicate_answers)]:
        buckets=collections.defaultdict(list)
        for m in measures:buckets[m[key]].append(dict(id=m['id'],split=m['split']))
        dest.extend(v for k,v in buckets.items() if len(v)>1)
    def grams(s):
        words=s.split();return set(tuple(words[i:i+5]) for i in range(len(words)-4))
    for a in [m for m in measures if m['split']=='train']:
        ga=grams(a['normalized_prompt'])
        for b in [m for m in measures if m['split']=='test']:
            gb=grams(b['normalized_prompt']); score=len(ga&gb)/max(1,min(len(ga),len(gb)))
            if score>=.35:near.append(dict(train=a['id'],test=b['id'],fivegram_containment=score))
    # Recheck the corrected prompt AND target against the known protected inputs.
    from audit_turkish_source_overlap import grams as protected_grams
    protected = set()
    cohort = ROOT/'experiments/turkish-capability/lfm3-1.7b/exp-004-cpt-cont-100m/results-local/official-general-500-v01/cetvel/scored-samples.jsonl'
    for raw in cohort.read_text(encoding='utf-8').splitlines():
        item=json.loads(raw); doc=item['document']
        texts=[item['semantic_prompt']] + [doc[k] for k in ['question','context','text','source'] if isinstance(doc.get(k),str)] + list(doc.get('translation',{}).values())
        for text in texts:
            protected.update(protected_grams(text))
    from audit_turkish_sources import messages
    for raw in (OUT/'raw-local/occam/data/validation.jsonl').read_text(encoding='utf-8').splitlines():
        for msg in messages(json.loads(raw)):
            if msg['role']=='user': protected.update(protected_grams(msg['content']))
    protected_hits=[]
    for row in allrows:
        text='\n'.join(m['content'] for m in row['messages'] if m['role']=='user')+'\n'+row['reviewed_target']
        matches=protected_grams(text)&protected
        if matches: protected_hits.append(dict(id=row['id'],matched_12grams=len(matches)))
    report=dict(exported_at_utc=snapshot['exported_at_utc'], tokenizer_revision='0dc4268b561499c648c7ba7c9466bf3d8d01517a',
        tokenizer_sha256=TOKENIZER_HASH, scope='Raw semantic content, no chat template or special tokens. Final target only; earlier assistant turns are context. Quantiles use lower order statistic; median uses midpoint.',
        groups=groups, exact_prompt_duplicates=duplicate_prompts, exact_final_duplicates=duplicate_answers,
        cross_split_fivegram_candidates=near,protected_input_12gram_hits=protected_hits,excluded=excluded,
        longest_targets=sorted([{k:m[k] for k in ['id','split','source','final_tokens','reasoning_tokens','target_tokens']} for m in measures],key=lambda m:m['target_tokens'],reverse=True)[:10])
    dump(DEST/'eda.json',report)
    lines(DEST/'row-metrics.jsonl',[{k:v for k,v in m.items() if not k.startswith('normalized_')} for m in measures])
    output=['# Owner-reviewed Turkish SFT pilot v01','',
        'All 100 Argilla records were submitted. Owner edits replace the complete final target; corrected prompts replace the last user turn. Original fields, exact corrections, ratings and response statuses remain in the snapshot. Argilla was read only and its datasets remain available.','',
        'The 80 training candidates and 20 held-out test records retain their frozen assignments. Test references, corrections and variants must never enter training or guide checkpoint selection. This is a small source-balanced calibration pilot, not a representative general Turkish benchmark.','',
        '## Length and exposure balance','',
        '| Split/source | Rows | Edited | Prompt median | Final median / p90 | Reasoning rows | Target tokens | Target share within split |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for key,g in groups.items():
        split=key.split('/')[0]; total=groups[f'{split}/all']['lengths']['target_tokens']['total']
        output.append(f"| {key} | {g['rows']} | {g['decisions'].get('edit',0)} | {g['lengths']['prompt_tokens']['median']} | {g['lengths']['final_tokens']['median']} / {g['lengths']['final_tokens']['p90']} | {g['reasoning_rows']} | {g['lengths']['target_tokens']['total']} | {g['lengths']['target_tokens']['total']/total:.1%} |")
    output += ['', 'Counts are source-balanced by design (20/source in train, 5/source in test); token exposure need not be balanced. Training should choose capability and response-length targets deliberately, rather than forcing equal lengths or weighting sources by their raw corpus size. System tokens are reported separately and are not supervised target tokens.', '',
        '## Before and after corrections','', '| Split | Original target tokens | Reviewed target tokens | Change | Prompt edits |', '|---|---:|---:|---:|---:|']
    for split in NAMES:
        g=groups[f'{split}/all'];before=g['lengths']['original_target_tokens']['total'];after=g['lengths']['target_tokens']['total']
        output.append(f"| {split} | {before} | {after} | {after/before-1:+.1%} | {g['prompt_edits']} |")
    output += ['', '## Other exploratory features','', '| Split | Final 0–64 / 65–256 / 257–512 / 513+ tokens | Multi-turn | Headings | Lists | Code fences | JSON-like | Tables | Raw >4096 / >8192 |', '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for split in NAMES:
        g=groups[f'{split}/all'];f=g['format_indicators'];bins=g['final_length_bins']
        output.append(f"| {split} | {' / '.join(str(bins.get(k,0)) for k in ['0-64','65-256','257-512','513+'])} | {g['multi_turn_rows']} | {f['markdown_heading']} | {f['list_format']} | {f['code_fence']} | {f['json_object']} | {f['table']} | {g['above_raw_4096']} / {g['above_raw_8192']} |")
    output += ['', 'Format features are overlapping lexical indicators, not verified task coverage. Source category counts and per-source length distributions are in `eda.json`; they retain upstream labels and are not an adjudicated capability taxonomy.', '',
        '## Descriptive capability coverage', '',
        'Agent-assigned primary task labels describe reviewed prompts. They are not owner-adjudicated or evidence of correctness. Labels are frozen in `capability-audit.json`. Technical subject matter does not imply executable coding; JSON-like detection below includes arrays.', '',
        '| Primary capability | Train | Test |', '|---|---:|---:|']
    categories=sorted(set(labels.values()))
    for category in categories:
        output.append(f"| {category} | {groups['train/all']['primary_capabilities'].get(category,0)} | {groups['test/all']['primary_capabilities'].get(category,0)} |")
    output += ['',
        '## Reasoning and direct answers','',
        'Owner-confirmed policy: simple/verbal questions can intentionally have no separate reasoning. An edited answer without tags does not inherit its original reasoning. Both `<thinking>` and `<think>` are parsed into `worked_solution`; `messages` holds the final answer. `reviewed_target` preserves the exact submitted target. Never concatenate both representations or train a reasoning-required system prompt against a direct-only projection without adapting the instruction.', '',
        'Source system prompts are preserved for provenance. Several request exhaustive detail or mandatory reasoning, while owner edits intentionally teach concise or direct answers. These rows need a separately versioned system-instruction normalization and native-template/loss-mask preflight before training. This export is semantic reviewed data, not an immediately runnable trainer dataset. Final-only supervision also preserves Occam\'s policy for multi-turn rows.', '',
        '## Validation and limitations','',
        f"Exact normalized prompt duplicate groups: {len(duplicate_prompts)}. Exact final-answer duplicate groups: {len(duplicate_answers)}. Cross-split five-word containment candidates (>=0.35): {len(near)}. Records with 12-word matches to known protected inputs: {len(protected_hits)}. Excluded records: {len(excluded)}.", '',
        'Protected-input checking covers edited prompts and targets against the known CETVEL-500 cohort and public Occam validation prompts. Lexical checks do not establish semantic/cross-lingual benchmark clearance. Correctness ratings express owner approval, not an independent proof of every claim. No rows were silently rebalanced, rewritten, or dropped.', '',
        '### Targeted content issues to revisit', '',
        '- `atlas:train.chat.jsonl:312719`: prompt says 20% profit margin, but reasoning and final use 20% markup. Under margin = profit / sale price, 450 / 0.8 * 1.2 = 675 TL; 648 TL requires a markup interpretation. Clarify the prompt or repair both reasoning and final.',
        '- `cot:train.jsonl:247`: introducing some taxes and reducing others is not necessarily a contradiction. The prompt does not establish the same tax/base/time, so the assertion that both cannot be true is too strong. Repair the problem/options or qualify the conclusion.',
        '- `atlas:train.chat.jsonl:213455`: the prompt does not specify unauthorized access. The answer leads with refusal of unauthorized access; review whether a question about authorization or a legitimate HR-access route would better teach selective clarification.', '',
        'These are targeted agent findings, not an exhaustive second correctness review. Submitted owner text is preserved; none is automatically rejected or silently changed. Resolve confirmed issues before a training-ready release. Absence of reasoning tags is intentional owner policy and is not a defect.', '',
        'The next growth batch should use a capability taxonomy and fill measured gaps (particularly multi-turn interaction, coding, bilingual translation and varying context lengths) after semantic review confirms actual coverage. Keep concise, medium and long answers when the task calls for them. Keep direct versus reasoning modes distinct; do not select verbose answers just to equalize token totals.', '',
        '## Files and reconstruction','',
        '- `train.jsonl` / `test.jsonl`: applied owner corrections, source lineage and separate worked solutions.',
        '- `argilla-submitted-snapshot.json`: complete reviewed records and original UI fields, with no credentials.',
        '- `row-metrics.jsonl` / `eda.json`: measured features, distributions, duplicate candidates and longest targets.',
        '- `manifest.json`: hashes and policy; `excluded.jsonl`: excluded decisions (empty if all accepted).',
        '- Run `python scripts/datasets/export_turkish_reviewed_pilot.py`; the frozen snapshot is reused. Pinned local review packets and tokenizer are required to reconstruct. No live annotations are overwritten.', '']
    (DEST/'README.md').write_text('\n'.join(output),encoding='utf-8', newline='\n')
    dump(DEST/'manifest.json',dict(exported_at_utc=snapshot['exported_at_utc'],counts=dict(collections.Counter(r['split'] for r in allrows)),
        policy='Owner edits applied verbatim; reasoning optional; final assistant only; protected test; source systems preserved pending objective normalization',
        source_packet_sha256={s:filehash(OUT/f'review-local/review-100-{s}.jsonl') for s in NAMES},
        script_sha256=filehash(Path(__file__)),files={p.name:filehash(p) for p in sorted(DEST.iterdir()) if p.is_file() and p.name!='manifest.json'}))
    print(json.dumps(dict(counts={s:groups[f'{s}/all'] for s in NAMES},duplicates=duplicate_prompts,near=near),ensure_ascii=True))


if __name__=='__main__':
    main()
