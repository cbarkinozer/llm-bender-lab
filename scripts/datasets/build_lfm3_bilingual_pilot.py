"""Build the four-direction bilingual SFT pilot (160 task groups x 4 directions = 640 rows) from the frozen
reviewed Turkish pilot160 train set plus the hand-authored translation files.

No model/API is called: translations were written directly by the Claude Code session (claude-sonnet-5-5) and are
stored in translations/part-NNN.txt. This script is deterministic; re-running must reproduce every file byte for byte.

  python scripts/datasets/build_lfm3_bilingual_pilot.py
"""
import glob
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bilingual_pilot_common import (BASE, DIRECTIONS, INSTRUCTION, NEUTRAL_CONTENT_GROUPS, PILOT, PRESERVE_ANSWER_GROUPS, PRESERVE_EXPLAIN_GROUPS, instruction_for, SYSTEM, SYSTEM_TR, freeze, json_bytes,
                                    jsonl_bytes, parse_translation_file, read_jsonl, sha256_file, sha256_text,
                                    with_instruction)

SOURCE = BASE / 'sft-pilot160-v01/train.jsonl'
SOURCE_SHA = 'e8bd148d2a3947dd7870ab404e3a4b402c792c7b0983b7ed8f8731325d5747b9'  # frozen train.jsonl (manifest)
OUT = PILOT / 'data'
BUILD_DATE = '2026-11-17'
TRANSLATOR = 'claude-sonnet-5-5 (Claude Code session; direct translation, no external API or service called)'

# Agent-descriptive capability labels for the 80 rows that carry none in the source (g081-g160). Not owner-adjudicated.
NEW80_CATEGORY = {
    81: 'rewriting_and_summary', 82: 'arithmetic_and_constraints', 83: 'clarification_and_uncertainty',
    84: 'arithmetic_and_constraints', 85: 'planning_and_advice', 86: 'planning_and_advice',
    87: 'logic_and_critical_reasoning', 88: 'planning_and_advice', 89: 'clarification_and_uncertainty',
    90: 'clarification_and_uncertainty', 91: 'logic_and_critical_reasoning', 92: 'clarification_and_uncertainty',
    93: 'rewriting_and_summary', 94: 'legal_explanation', 95: 'legal_explanation', 96: 'grounded_comprehension',
    97: 'structured_extraction', 98: 'structured_extraction', 99: 'assistant_identity', 100: 'rewriting_and_summary',
    101: 'rewriting_and_summary', 102: 'legal_explanation', 103: 'rewriting_and_summary', 104: 'planning_and_advice',
    105: 'logic_and_critical_reasoning', 106: 'clarification_and_uncertainty', 107: 'conceptual_explanation',
    108: 'arithmetic_and_constraints', 109: 'arithmetic_and_constraints', 110: 'conceptual_explanation',
    111: 'conceptual_explanation', 112: 'legal_explanation', 113: 'planning_and_advice', 114: 'conceptual_explanation',
    115: 'rewriting_and_summary', 116: 'arithmetic_and_constraints', 117: 'rewriting_and_summary',
    118: 'arithmetic_and_constraints', 119: 'grammar_and_morphology', 120: 'arithmetic_and_constraints',
    121: 'rewriting_and_summary', 122: 'planning_and_advice', 123: 'grammar_and_morphology', 124: 'planning_and_advice',
    125: 'logic_and_critical_reasoning', 126: 'planning_and_advice', 127: 'arithmetic_and_constraints',
    128: 'grounded_comprehension', 129: 'arithmetic_and_constraints', 130: 'grammar_and_morphology',
    131: 'arithmetic_and_constraints', 132: 'conceptual_explanation', 133: 'assistant_identity',
    134: 'logic_and_critical_reasoning', 135: 'grammar_and_morphology', 136: 'arithmetic_and_constraints',
    137: 'planning_and_advice', 138: 'arithmetic_and_constraints', 139: 'legal_explanation',
    140: 'arithmetic_and_constraints', 141: 'planning_and_advice', 142: 'logic_and_critical_reasoning',
    143: 'grounded_comprehension', 144: 'logic_and_critical_reasoning', 145: 'rewriting_and_summary',
    146: 'rewriting_and_summary', 147: 'grounded_comprehension', 148: 'grounded_comprehension',
    149: 'planning_and_advice', 150: 'arithmetic_and_constraints', 151: 'arithmetic_and_constraints',
    152: 'clarification_and_uncertainty', 153: 'arithmetic_and_constraints', 154: 'conceptual_explanation',
    155: 'conceptual_explanation', 156: 'arithmetic_and_constraints', 157: 'planning_and_advice',
    158: 'clarification_and_uncertainty', 159: 'legal_explanation', 160: 'planning_and_advice',
}
# Groups whose Turkish object-language text is kept verbatim while only explanations change language.


def tail_whitespace(text):
    return text[len(text.rstrip()):]


def load_translations():
    out, files = {}, {}
    for path in sorted(glob.glob(str(PILOT / 'translations/part-*.txt'))):
        part = Path(path).name
        files[part] = sha256_file(path)
        for key, entry in parse_translation_file(path).items():
            assert key not in out, f'duplicate translation for {key}'
            entry['part'] = part
            out[key] = entry
    return out, files


def build():
    assert sha256_file(SOURCE) == SOURCE_SHA, 'frozen source train.jsonl changed'
    raw_lines = SOURCE.read_text(encoding='utf-8').splitlines()
    rows = [json.loads(l) for l in raw_lines]
    assert len(rows) == 160
    translations, part_hashes = load_translations()
    assert set(translations) == {f'g{i:03d}' for i in range(1, 161)}
    originals, train = [], []
    for n, (raw, row) in enumerate(zip(raw_lines, rows), 1):
        key = f'g{n:03d}'
        group = f'bp01-{key}'
        tr = translations[key]
        assert tr['source_id'] == row['id']
        ms = row['messages']
        assert [m['role'] for m in ms] == ['system', 'user', 'assistant'] and ms[0]['content'] == SYSTEM_TR
        user_tr, asst_tr, ws_tr = ms[1]['content'], ms[2]['content'], row['worked_solution']
        assert (tr['reasoning'] is not None) == bool(ws_tr)
        # Source-hash-pinned reviewed text, kept separate for provenance (reviewed_target/<thinking> notation not copied).
        category = row.get('primary_capability') or NEW80_CATEGORY[n]
        basis = row.get('capability_label_basis') or 'agent-descriptive label added by this pilot; not owner-adjudicated'
        originals.append(dict(
            group_id=group, source_row_id=row['id'], source_key=row['source_key'], source=row['source'],
            original_row_sha256=sha256_text(raw), category=category, capability_label_basis=basis,
            system=ms[0]['content'], user=user_tr, assistant=asst_tr, worked_solution=ws_tr,
            reviewed_target_sha256=sha256_text(row['reviewed_target']),
            review_decision=row['review'].get('decision'), review_ratings=row['review'].get('ratings'),
            review_approval_basis=row['review'].get('approval_basis'),
            source_user_sha256=sha256_text(user_tr), source_assistant_sha256=sha256_text(asst_tr),
            source_reasoning_sha256=sha256_text(ws_tr) if ws_tr else None,
            source_file='experiments/turkish-capability/lfm3-1.7b/sft-pilot160-v01/train.jsonl',
            source_file_sha256=SOURCE_SHA, source_line_1based=n))
        en = dict(user=tr['user'] + tail_whitespace(user_tr), assistant=tr['assistant'] + tail_whitespace(asst_tr),
                  reasoning=(tr['reasoning'] + tail_whitespace(ws_tr)) if ws_tr else None)
        flags = tr['flags']
        for direction in DIRECTIONS:
            src, dst = direction.split('-')
            user_base = user_tr if src == 'tr' else en['user']
            asst = asst_tr if dst == 'tr' else en['assistant']
            ws = (ws_tr if dst == 'tr' else en['reasoning'])
            variant, instruction_text = instruction_for(key, src, dst)
            user = with_instruction(user_base, src, dst, instruction_text)
            assert user.startswith(user_base) and user[len(user_base):].lstrip('\n') == instruction_text
            translated = {'input': src == 'en', 'output': dst == 'en', 'reasoning': bool(ws_tr) and dst == 'en',
                          'system': src == 'en'}
            kind = ('identity' if direction == 'tr-tr' else 'translate_input' if direction == 'en-tr'
                    else 'translate_output' if direction == 'tr-en' else 'translate_input_and_output')
            effect = ('preserve_turkish_object' if variant != 'standard' else
                      'neutral_content' if dst == 'en' and key in NEUTRAL_CONTENT_GROUPS else 'full')
            train.append(dict(
                id=f'bp01-{key}-{direction}', group_id=group, canonical_task_id=group, split='train',
                direction=direction, input_language=src, output_language=dst,
                messages=[dict(role='system', content=SYSTEM[src]), dict(role='user', content=user),
                          dict(role='assistant', content=asst)],
                worked_solution=ws,
                reasoning_language=dst if ws else None, has_reasoning=bool(ws),
                category=category, capability_label_basis=basis, source_key=row['source_key'],
                language_instruction=dict(text=instruction_text, position='user_suffix', language=src, variant=variant),
                output_language_effect=effect,
                source_row_id=row['id'], original_source=row['source'], original_row_sha256=sha256_text(raw),
                source_user_sha256=sha256_text(user_tr), source_assistant_sha256=sha256_text(asst_tr),
                source_reasoning_sha256=sha256_text(ws_tr) if ws_tr else None,
                transformation=dict(kind=kind, translated=translated, translator=TRANSLATOR if kind != 'identity' else None,
                                    translated_on=BUILD_DATE if kind != 'identity' else None,
                                    translation_file=f"translations/{tr['part']}" if kind != 'identity' else None,
                                    translation_file_sha256=part_hashes[tr['part']] if kind != 'identity' else None,
                                    system_prompt='original reviewed Turkish system prompt' if src == 'tr'
                                    else 'English rendering of the reviewed system prompt (bilingual_pilot_common.SYSTEM_EN)',
                                    language_instruction_added=True, trailing_whitespace='copied from the reviewed original',
                                    translation_flag_types=sorted({f['type'] for f in flags}),
                                    translation_flag_max_severity=(max((f['severity'] for f in flags), default=None,
                                                                       key=['info', 'low', 'medium', 'high'].index))),
                generation_method='human-reviewed original' if kind == 'identity' else 'transformed (agent translation of human-reviewed original)',
                use_restriction=None if kind == 'identity' else 'RESTRICTED_PENDING_PROVIDER_TERMS: translated text must not be used for training or release until TERMS-RESTRICTION.md is resolved',
                intended_use='training-candidate', quality_status='pilot; owner translation review pending'))
    return originals, train, part_hashes, translations


def main():
    originals, train, part_hashes, translations = build()
    assert len(originals) == 160 and len(train) == 640 and len({r['id'] for r in train}) == 640
    OUT.mkdir(parents=True, exist_ok=True)
    flags = []
    for key in sorted(translations):
        for f in translations[key]['flags']:
            flags.append(dict(group_id=f'bp01-{key}', source_row_id=translations[key]['source_id'], **f))
    arm_a = [r for r in train if r['direction'] == 'tr-tr']
    files = {'train.jsonl': jsonl_bytes(train), 'source-originals.jsonl': jsonl_bytes(originals),
             'train-arm-a-tr-only.jsonl': jsonl_bytes(arm_a), 'translation-flags.jsonl': jsonl_bytes(flags)}
    for name, data in files.items():
        freeze(OUT / name, data)
    counts = {d: sum(r['direction'] == d for r in train) for d in DIRECTIONS}
    manifest = dict(
        status='built; see validation/ for reports (release-manifest.json is written after validation)', dataset='bilingual-pilot-v01', built_on=BUILD_DATE,
        builder='scripts/datasets/build_lfm3_bilingual_pilot.py', common='scripts/datasets/bilingual_pilot_common.py',
        task_groups=160, rows=640, per_direction=counts, directions=DIRECTIONS,
        source=dict(file='experiments/turkish-capability/lfm3-1.7b/sft-pilot160-v01/train.jsonl', sha256=SOURCE_SHA,
                    note='frozen reviewed pilot160 train set; old20 test/dev20/xling packets never used as source'),
        translation=dict(translator=TRANSLATOR, external_services_called=False, files=part_hashes,
                         flags_total=len(flags)),
        seeds=dict(builder='none (deterministic; no randomness)'),
        language_instruction={f'{a}-{b}': t for (a, b), t in INSTRUCTION.items()},
        system_prompts=dict(tr='reviewed original (unchanged)', en=SYSTEM['en']),
        files={name: dict(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)) for name, data in files.items()},
        split='all 640 rows are split=train; all four directions of a task share group_id/split (no row-level splitting)',
        schema_notes='messages = system/user/assistant; reasoning in worked_solution (same field as pilot160), null for direct answers; '
                    'no <think>/<thinking> tags in semantic fields; native template applied only at preprocessing.',
        license_and_terms=dict(
            source_licenses={'occam': 'Apache-2.0 (cbarkinozer/Occam-Turkish-Response-SFT@947850d4)', 'sft': 'MIT declared (AlicanKiraz0/Turkish-SFT-Dataset-v1.0@5a5a852a)',
                             'atlas': 'MIT declared, qualified (AlicanKiraz0/Turkce-Atlas-Instruct@c387738c)', 'cot': 'Apache-2.0 declared (AlicanKiraz0/Turkish-CoT-Instruct-Dataset@3473e6c6)'},
            source_status='Inherited from sft-pilot160-v01 / source-audit-v01: documentary review found no prohibited use but did NOT clear training/release eligibility; unresolved.',
            translation_provider='Anthropic model claude-sonnet-5-5 via Claude Code, on 2026-11-17; no external paid API called.',
            provider_terms_checked_2026_11_18={
                'commercial_terms (effective 2025-06-17) D.4': 'Customer may not use the Services "to build a competing product or service, including to train competing AI models".',
                'consumer_terms (effective 2025-10-08) s.3': 'Prohibits using the Services "to develop any products or services that compete with our Services" and "to develop or train any artificial intelligence or machine learning algorithms or models".'},
            terms_conclusion='RESTRICTED_PENDING_CLARIFICATION (account type: Free/Pro/Max/Ultra => Consumer Terms s.3 item 2; see TERMS-RESTRICTION.md). UNRESOLVED: whether fine-tuning LiquidAI LFM3 on these translations is permitted under the applicable Anthropic terms (account type unknown to the agent). Owner must confirm before training or publishing. See UNRESOLVED-DECISIONS.md #1.'),
        limitations=['Translations are agent-authored and not owner-reviewed.',
                     '12 groups use a preserve-Turkish-text instruction variant for EN output; 3 groups have language-neutral answers (JSON/names).',
                     'EN system prompt drops the word "Turkish"; see unresolved decisions.'])
    freeze(PILOT / 'build-manifest.json', json_bytes(manifest))
    print('built', counts, {k: v['sha256'][:12] for k, v in manifest['files'].items()})


if __name__ == '__main__':
    main()
