"""CPU self-test of the eval v2 scoring pipeline using synthetic model outputs.

Builds an oracle run (always right), a degraded run (symbolic mostly wrong, some tool calls missing,
Turkish math format drift) and a thinking-on run, then checks per-family numbers and paired statistics.
No model, GPU or network is used. Requires the packets from build_lfm3_eval_v2.py.
"""
import json
from pathlib import Path
import random
import sys
import tempfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'datasets'))
import lfm3_eval_v2_scoring as scoring  # noqa: E402
import score_lfm3_eval_v2 as scorer  # noqa: E402
import build_lfm3_eval_v2 as builder  # noqa: E402


def oracle_answer(row, rng, degrade, thinking):
    prefix = 'Let me think.</think>' if thinking else ''
    family, lang, gold = row['family'], row['language'], row.get('gold')
    if family == 'math':
        marker = 'Final answer' if lang == 'en' else 'Nihai cevap'
        value = gold
        if degrade and lang == 'tr' and rng.random() < .5:
            value = str(int(gold) + 1)
        text = f'Step 1... so the total is {value}.\n{marker}: {value}'
    elif family == 'symbolic':
        value = gold if not degrade or rng.random() < .2 else str(int(gold) + 7)
        text = f'{value}'
    else:
        if degrade and rng.random() < .3:
            text = 'I cannot call a function for this.'
        else:
            calls = [(name, {k: builder.first_value(v) for k, v in params.items() if v[0] != ''})
                     for entry in row['gold_calls'] for name, params in entry.items()]
            text = ''.join(scoring.render_call_xml(n, a) for n, a in calls)
    return prefix + text + '<|im_end|>'


def write_run(directory, packets, name, degrade, thinking, seed=1):
    directory.mkdir(parents=True)
    rng = random.Random(seed)
    (directory / 'run-manifest.json').write_text(json.dumps(dict(name=name, thinking='on' if thinking else 'off')))
    with (directory / 'answers-seed3407.jsonl').open('w', encoding='utf-8') as f:
        for row in packets.values():
            f.write(json.dumps(dict(id=row['id'], raw_output=oracle_answer(row, rng, degrade, thinking),
                                    generated_tokens=50, finish_reason='eos', hit_max_new_tokens=False)) + '\n')


def main():
    manifest = json.loads((builder.EXP / 'manifest-core.json').read_text(encoding='utf-8'))
    packets = scorer.load_packets(builder.EXP / 'data-local', manifest)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        write_run(tmp / 'oracle', packets, 'oracle', False, False)
        write_run(tmp / 'oracle-think', packets, 'oracle-think', False, True)
        write_run(tmp / 'degraded', packets, 'degraded', True, False)
        data = builder.EXP / 'data-local'
        oracle = scorer.score_run(tmp / 'oracle', data, manifest)['seeds']['3407']
        think = scorer.score_run(tmp / 'oracle-think', data, manifest)['seeds']['3407']
        degraded = scorer.score_run(tmp / 'degraded', data, manifest)['seeds']['3407']
        for key, value in oracle['summary'].items():
            assert value['accuracy'] == 1.0, (key, value)
        assert oracle['summary']['math/en']['marker_parse_rate'] == 1.0
        assert oracle['summary']['symbolic/tr']['number_only_rate'] == 1.0
        assert all(v['thinking_closure_rate'] == 1.0 for v in think['summary'].values())
        assert all(v['accuracy'] == 1.0 for v in think['summary'].values())
        assert degraded['summary']['symbolic/en']['accuracy'] < .4
        assert .3 < degraded['summary']['math/tr']['accuracy'] < .7 and degraded['summary']['math/en']['accuracy'] == 1.0
        assert degraded['summary']['toolcall/en']['errors']['no_tool_call'] > 5
        assert degraded['tr_en_gap']['math']['tr_minus_en'] < -.2
        result = scorer.compare(scorer.load_scores(tmp / 'oracle'), scorer.load_scores(tmp / 'degraded'))
        sym = result['symbolic/en']
        assert sym['delta'] < -.5 and sym['bootstrap95'][1] < 0 and sym['mcnemar_p'] < .001 and sym['gained'] == 0
        assert scorer.mcnemar_exact(5, 5) == 1.0 and scorer.wilson(8, 8)[0] > .6
        # unclosed thinking must score as a failure, not as a parse accident
        row = next(r for r in packets.values() if r['family'] == 'symbolic')
        assert not scorer.score_row(row, dict(raw_output='still thinking ' + row['gold']), True)['correct']
    print('eval v2 pipeline self-test passed;', {k: v['n'] for k, v in oracle['summary'].items()})


if __name__ == '__main__':
    main()
