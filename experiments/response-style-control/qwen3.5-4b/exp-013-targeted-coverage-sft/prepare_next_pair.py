"""CPU-only C/D preparation. Drafts cannot produce approved training gates."""
import copy
import csv
import importlib.util
import io
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
D = ROOT / 'exp-014-targeted-duration-sft'
PREVIOUS = ROOT / 'exp-012-coverage-ablation'
# Reuse original hash verification, leakage corpus, tokenization and immutable
# writers. Load new specs by explicit path to avoid the old candidate_specs name.
spec = importlib.util.spec_from_file_location('next_candidate_specs', HERE/'candidate_specs.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
SPECS = module.SPECS
sys.path.insert(0, str(PREVIOUS))
from prepare_pair import (original, sha, encoded, jsonl, save, load_rows,
    audit, tokenize, SOURCE_HASHES, PARENT, views, similarity)
# Older helpers insert their directories into sys.path. Restore this experiment
# first so export_review/import_review cannot resolve an older namesake module.
sys.path.insert(0, str(HERE))


def candidates():
    rows = []
    assert len(SPECS) == 12
    for i, (category, scenario, replaced, prompt, target, criteria) in enumerate(SPECS, 1):
        messages = [dict(role='user', content=prompt)]
        rows.append(dict(id=f'tc-{i:03}', split='train', evaluation_only=False,
            category=category, subtype=scenario, scenario_group_id='targeted-'+scenario,
            messages=messages, prompt_tr='user: '+prompt, desired_answer=target,
            evaluation_criteria=criteria, replaces_id=replaced,
            input_messages_sha256=sha(json.dumps(messages, ensure_ascii=False, separators=(',',':')).encode()),
            source_path='exp-013-targeted-coverage-sft/candidate_specs.py',
            source_id=f'tc-{i:03}', origin='new-project-agent-authored',
            authored_date='2026-10-03', review_decision='pending',
            answer_status='draft-awaiting-human-review', dataset_version='targeted-draft-v2',
            loss_policy='final assistant only; all earlier turns masked'))
    assert len({r['replaces_id'] for r in rows}) == 12
    return rows


def assemble(new):
    train, validation = original()
    mapping = {r['replaces_id']:r for r in new}
    assert set(mapping) <= {r['id'] for r in train} and len(mapping) == 12
    result = [mapping.get(r['id'], r) for r in train]
    assert len(result) == len({r['id'] for r in result}) == 80
    retained = [r for r in result if r['id'].startswith('me-')]
    assert len(retained) == 68 and all(r in train for r in retained)
    for row in train:
        if int(row['id'].split('-')[1]) > 40:
            assert row in retained, 'Preserve all original higher-level rows'
    return result, validation


def leakage(new):
    train, validation = original()
    report = audit(new, train, validation)
    report['candidate_rows'] = 12
    report['semantic_review'] = (
        'New fictional scenarios: ceramic finishes, theater roles, battery runtime, '
        'botanical collections, projector diagnosis, folder permission logs, podcast '
        'cancellation motive, translation version control, polite-address agreement, '
        'doctoral education versus doctor job, insured art loan, tentative festival. '
        'No validation prompt, solution, paraphrase, number/entity substitution or '
        'cafe-sign/morning-departure/desk-layout/home-feeling/exam-venting setting used. '
        'Behavior-level error taxonomy informed the brief, not item-level solutions. '
        'Human review pending. me-089 reference remains disputed and untouched.')
    previous = load_rows(PREVIOUS/'data-reviewed-v1/train-reviewed.jsonl')
    previous_new = [r for r in previous if r['id'].startswith('bc-')]
    flags = []
    closest = []
    for row in new:
        scores = []
        for other in previous_new:
            score = max(similarity(a, b) for a in views(row) for b in views(other))
            scores.append(dict(candidate=row['id'], other_id=other['id'], similarity=round(score,4)))
            if score >= .78:
                flags.append(scores[-1])
        closest.extend(sorted(scores, key=lambda x:x['similarity'], reverse=True)[:1])
    assert not flags, flags
    report.update(previous_B_rows_checked=len(previous_new), previous_B_near_flags=flags,
                  closest_previous_B_pairs=closest)
    return report


def make_config(experiment_id, approved=False, train_hash=None):
    config = json.loads((ROOT/'exp-011-duration-ablation/config.yaml').read_text(encoding='utf-8'))
    is_d = experiment_id == D.name
    assert experiment_id in (HERE.name, D.name)
    config.update(experiment_id=experiment_id, parent=HERE.name if is_d else 'exp-011-duration-ablation',
                  status='prepared-needs-gpu-gates' if approved else 'blocked-human-review')
    config['dataset'].update(train='../'+HERE.name+'/data-reviewed-v1/train-reviewed.jsonl',
        validation='reviewed-v2/validation-reviewed.jsonl', review_required=not approved,
        review_status='12-human-approved-argilla' if approved else 'pending-12-candidates')
    config['dataset']['hashes']['train-reviewed.jsonl'] = train_hash if approved else 'UNAPPROVED-DRAFT-NOT-A-TRAINING-HASH'
    config['training'].update(epochs=6 if is_d else 4, expected_optimizer_steps=60 if is_d else 40)
    config['tracking']['run_name'] = 'exp014-sft-targeted-80rows-6ep' if is_d else 'exp013-sft-targeted-80rows-4ep'
    config['notes'] = [
        'Fresh pinned base independently; do not initialize from any saved adapter.',
        'C vs A: retain 68 original rows and replace 12; all original rows above me-040 unchanged.',
        'D vs C: exact same reviewed80 rows, epochs4 -> 6; cosine trajectory extends.',
        'Both configs resolve dataset paths against shared exp009 trainer directory.',
        'Final scheduled adapter preselected; no best-checkpoint selection from20 development items.',
        'Same generation settings as saved A; no extra system prompt; HF/Unsloth, not vLLM.',
        'Repeated20 development items are not an independent final test; me-089 reference disputed.',
        'No inherited smoke/overfit/reload waiver. New GPU gates or explicit scoped user waiver required.',
        'Token exposure differs vs A. Record it, do not attribute all changes to isolated data quality.',
    ]
    return config


def prepare():
    new = candidates()
    draft, validation = assemble(new)
    leak = leakage(new)
    output = HERE/'data-draft-v2'
    save(output/'candidates-12.jsonl', jsonl(new))
    save(output/'train-reviewed.jsonl', jsonl(draft))
    save(output/'validation-reviewed.jsonl', (PARENT/'reviewed-v2/validation-reviewed.jsonl').read_bytes())
    save(output/'leakage-report.json', encoded(leak))
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=['id','category','replaces_id','prompt_tr','desired_answer','evaluation_criteria'],
                            extrasaction='ignore', lineterminator='\n')
    writer.writeheader()
    writer.writerows(new)
    save(output/'candidates-12.csv', stream.getvalue().encode('utf-8-sig'))
    config_c, config_d = make_config(HERE.name), make_config(D.name)
    report = tokenize(draft+validation, HERE/'training-preflight-draft-v2', False, config_c)
    prepared = load_rows(HERE/'training-preflight-draft-v2/train-tokenized.jsonl')
    parent_prepared = {r['id']:r for r in load_rows(PARENT/'training-preflight-v1/train-tokenized.jsonl')}
    for row in prepared:
        if row['id'].startswith('me-'):
            assert row == parent_prepared[row['id']], row['id']
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(config_c['model']['name'], revision=config_c['model']['revision'])
    inspection = [dict(id=r['id'], input_ids=r['input_ids'], labels=r['labels'],
        full_text=tokenizer.decode(r['input_ids'], skip_special_tokens=False),
        supervised_text=tokenizer.decode([x for x in r['labels'] if x!=-100], skip_special_tokens=False))
        for r in prepared if r['id'].startswith('tc-')]
    save(HERE/'candidate-mask-inspection-v2.json', encoded(inspection))
    token_a = json.loads((ROOT/'exp-011-duration-ablation/training-preflight-v1/report.json').read_text(encoding='utf-8'))['split_stats']['train']['target']['total']
    token_c = report['split_stats']['train']['target']['total']
    save(HERE/'config.yaml', encoded(config_c))
    save(D/'config.yaml', encoded(config_d))
    manifest = dict(status='awaiting-human-review', training_started=False,
        retained_rows=68, new_rows=12, removed_ids=[r['replaces_id'] for r in new],
        original_hashes=SOURCE_HASHES, draft_train_sha256=sha(jsonl(draft)),
        category_counts_A=dict(Counter(r['category'] for r in original()[0])),
        category_counts_C_D=dict(Counter(r['category'] for r in draft)),
        authoring=dict(provider='OpenAI', interface='Codex project agent', exact_model='not exposed',
            sampling='not exposed', external_generation_api=False, date='2026-10-03',
            source_sha256=sha((HERE/'candidate_specs.py').read_bytes()),
            original_specs_sha256=sha((HERE/'candidate_specs_draft_v1.py').read_bytes()),
            permission='User requested project-local drafts; no third-party corpus copied; no public licensing claim'),
        replacement_policy='2 grammar, 4 extraction, 4 numeric/entity, 2 summary removed; preserve all other rows byte-semantically and in original positions',
        target_tokens_per_epoch=dict(A=token_a,C_D_draft=token_c),
        target_token_change_percent=round(100*(token_c-token_a)/token_a,2),
        files={p.name:sha(p.read_bytes()) for p in output.iterdir() if p.name!='manifest.json'})
    save(output/'manifest.json', encoded(manifest))
    save(HERE/'pair-preparation-report-v2.json', encoded(dict(
        status='draft-CPU-passed-human-review-required', training_started=False,
        candidates=12, retained=68, train_rows=80, validation_rows=20,
        shared_dataset_for_C_D=True, retained_tokenization_matches_A=True,
        validation_tokenization_matches_A=report['validation_tokenization_matches_parent'],
        expected_optimizer_steps=dict(C=40,D=60), truncated_rows=0,
        target_tokens_per_epoch=manifest['target_tokens_per_epoch'],
        target_token_change_percent=manifest['target_token_change_percent'],
        candidate_mask_inspection_sha256=sha((HERE/'candidate-mask-inspection-v2.json').read_bytes()),
        note='Historical shared tokenizer report uses human approval for B wording; for this pair it means all12 C/D candidates. This pair report is authoritative on review status.',
        remaining=['12 submitted human accept/rewrite reviews','reviewed-target re-tokenization and freeze',
                   'GPU actual-batch mask and environment checks','GPU smoke/reload and tiny-overfit unless explicitly waived for C/D','W&B authentication'],
        original_frozen_files_unchanged=True)))
    original()
    print(json.dumps(dict(status=manifest['status'],new_rows=12,retained_rows=68,
        target_tokens=manifest['target_tokens_per_epoch'],percent_change=manifest['target_token_change_percent'],
        original_validation_unchanged=True,training_started=False), ensure_ascii=True, indent=2))


if __name__ == '__main__':
    prepare()
