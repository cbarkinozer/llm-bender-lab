"""Deterministic scorers for LFM3 eval v2 (math word problems, symbolic arithmetic).

Scoring is separated from generation. Every record keeps the extraction method so
parser success and semantic correctness can be reported separately.
Run `python lfm3_eval_v2_scoring.py --self-test` to verify the extractors.
"""
import json
import re
import sys
from decimal import Decimal

SCORER_VERSION = 'eval-v2-scorer-2'
THINK_CLOSE = '</think>'
CONTROL_TOKENS = ('<|im_end|>', '<|endoftext|>', '<|startoftext|>')
# Explicit [iİ]/[ıiIİ] classes: re.I does not equate Turkish dotted capitals.
MARKER_RE = re.compile(r'(?:final\s+answer|n[iİ]ha[iİ]\s+(?:cevap|yan[ıiIİ]t))\s*[:：=\-–]?', re.I)
BOXED_RE = re.compile(r'\\boxed\s*\{')
NUMBER_RE = re.compile(r'-?\d[\d.,]*\d|-?\d')


def split_thinking(raw_output, thinking_enabled):
    """Return (answer_text, closed). The template prefills '<think>' (on) or '<think></think>' (off).

    closed is None when thinking was disabled, True/False when enabled.
    """
    text = raw_output
    for token in CONTROL_TOKENS:
        text = text.replace(token, '')
    if thinking_enabled:
        if THINK_CLOSE not in text:
            return '', False
        return text.rsplit(THINK_CLOSE, 1)[1].strip(), True
    if THINK_CLOSE in text:
        text = text.rsplit(THINK_CLOSE, 1)[1]
    return text.strip(), None


def parse_number(token, lang):
    """Parse one numeric token under the language's separator convention; None if invalid."""
    t = token.strip().replace('\u2212', '-')
    negative = t.startswith('-')
    t = t.lstrip('-')
    if re.fullmatch(r'\d{1,3}(,\d{3}){2,}(\.\d+)?', t):
        t = t.replace(',', '')  # unambiguous English grouping, accepted in both languages
    elif lang == 'en' and re.fullmatch(r'\d{1,3},\d{3}(\.\d+)?', t):
        t = t.replace(',', '')
    elif re.fullmatch(r'\d{1,3}(\.\d{3})+(,\d+)?', t) and (lang == 'tr' or ',' in t):
        t = t.replace('.', '').replace(',', '.')  # Turkish grouping
    elif lang == 'tr' and re.fullmatch(r'\d+,\d+', t):
        t = t.replace(',', '.')  # Turkish decimal comma
    elif not re.fullmatch(r'\d+(\.\d+)?', t):
        return None
    value = Decimal(t)
    return -value if negative else value


def _first_number(segment, lang):
    for match in NUMBER_RE.finditer(segment):
        value = parse_number(match.group(0), lang)
        if value is not None:
            return value
    return None


def extract_final_number(answer_text, lang):
    """Return (value, method). method: marker | boxed | fallback | none."""
    markers = list(MARKER_RE.finditer(answer_text))
    if markers:
        tail = answer_text[markers[-1].end():]
        line = tail.split('\n', 1)[0] or (tail.split('\n') + [''])[1]
        value = _first_number(line, lang)
        if value is not None:
            return value, 'marker'
    boxed = list(BOXED_RE.finditer(answer_text))
    if boxed:
        value = _first_number(answer_text[boxed[-1].end():].split('}', 1)[0], lang)
        if value is not None:
            return value, 'boxed'
    last = None
    for match in NUMBER_RE.finditer(answer_text):
        value = parse_number(match.group(0), lang)
        if value is not None:
            last = value
    return (last, 'fallback') if last is not None else (None, 'none')


def score_math(raw_output, gold, lang, thinking_enabled):
    answer, closed = split_thinking(raw_output, thinking_enabled)
    if closed is False:
        return dict(parsed=None, method='unclosed_thinking', correct_strict=False, correct_any=False,
                    thinking_closed=False, answer_chars=0)
    value, method = extract_final_number(answer, lang)
    equal = value is not None and value == Decimal(str(gold))
    return dict(parsed=None if value is None else str(value), method=method,
                correct_strict=bool(equal and method in ('marker', 'boxed')), correct_any=bool(equal),
                thinking_closed=closed, answer_chars=len(answer))


def score_symbolic(raw_output, gold, lang, thinking_enabled):
    """Symbolic arithmetic prompts ask for the number only; format compliance is tracked apart."""
    answer, closed = split_thinking(raw_output, thinking_enabled)
    if closed is False:
        return dict(parsed=None, correct=False, number_only=False, thinking_closed=False, answer_chars=0)
    cleaned = answer.strip().strip('*`$. ')
    only = parse_number(cleaned, lang) if re.fullmatch(r'-?\d[\d.,]*', cleaned) else None
    if only is not None:
        value, number_only = only, True
    else:
        value, _ = extract_final_number(answer, lang)
        number_only = False
    return dict(parsed=None if value is None else str(value),
                correct=bool(value is not None and value == Decimal(str(gold))),
                number_only=number_only, thinking_closed=closed, answer_chars=len(answer))


# ---------------------------------------------------------------- tool calls (BFCL-style AST match)
TOOL_BLOCK_RE = re.compile(r'<tool_call>(.*?)</tool_call>', re.S)
FUNCTION_RE = re.compile(r'<function=([^>\s]+)>(.*?)</function>', re.S)
PARAMETER_RE = re.compile(r'<parameter=([^>\s]+)>\n?(.*?)\n?</parameter>', re.S)


def _coerce(text, spec):
    kind = (spec or {}).get('type')
    value = text.strip()
    try:
        if kind in ('integer', 'number'):
            number = float(value)
            return int(number) if number.is_integer() else number
        if kind == 'boolean':
            return {'true': True, 'false': False}[value.lower()]
        if kind in ('array', 'object'):
            return json.loads(value)
    except (ValueError, KeyError):
        return value
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def parse_tool_calls(answer_text, tools):
    """Return (calls, fmt). calls: list of (name, args). fmt: xml | json | none | error.

    Accepts the template's own XML-style format and a JSON body inside <tool_call>.
    """
    schemas = {t['name']: (t.get('parameters') or {}).get('properties', {}) for t in tools}
    calls = []
    for block in TOOL_BLOCK_RE.findall(answer_text):
        found = FUNCTION_RE.search(block)
        if found:
            name, body = found.group(1), found.group(2)
            props = schemas.get(name, {})
            args = {k: _coerce(v, props.get(k)) for k, v in PARAMETER_RE.findall(body)}
            calls.append((name, args))
            continue
        try:
            data = json.loads(block.strip())
            args = data.get('arguments', data.get('parameters', {}))
            if isinstance(args, str):
                args = json.loads(args)
            calls.append((data['name'], args))
        except (ValueError, KeyError, TypeError, AttributeError):
            return calls, 'error'
    if not calls:
        return calls, 'none'
    return calls, 'xml' if '<function=' in answer_text else 'json'


def _norm_str(value):
    return re.sub(r'[\s,./\-_*^]', '', value.lower()).replace("'", '"')


def _equal(value, accepted):
    if isinstance(accepted, bool) or isinstance(value, bool):
        return value is accepted
    if isinstance(accepted, (int, float)) and isinstance(value, (int, float)):
        return abs(accepted - value) < 1e-9
    if isinstance(accepted, str) and isinstance(value, str):
        return _norm_str(accepted) == _norm_str(value)
    if isinstance(accepted, list) and isinstance(value, list):
        return len(accepted) == len(value) and all(_equal(v, a) for v, a in zip(value, accepted))
    if isinstance(accepted, dict) and isinstance(value, dict):
        return set(accepted) == set(value) and all(any(_equal(value[k], a) for a in accepted[k]) for k in accepted)
    return False


def call_matches(name, args, gold_entry, tools):
    """gold_entry: {function: {param: [acceptable values]}}; '' in the list marks an optional parameter."""
    (gold_name, gold_params), = gold_entry.items()
    if name != gold_name:
        return False
    schema = next(t for t in tools if t['name'] == gold_name).get('parameters') or {}
    props, required = schema.get('properties', {}), schema.get('required', [])
    if any(k not in props for k in args) or any(k not in args for k in required):
        return False
    for key, alternatives in gold_params.items():
        if key in args:
            if not any(_equal(args[key], a) for a in alternatives):
                return False
        elif '' not in alternatives:
            return False
    return all(k in gold_params for k in args)


def _assign(calls, gold, tools, used=()):
    if not gold:
        return True
    for index, (name, args) in enumerate(calls):
        if index not in used and call_matches(name, args, gold[0], tools):
            if _assign(calls, gold[1:], tools, used + (index,)):
                return True
    return False


def score_toolcall(raw_output, gold_calls, tools, thinking_enabled):
    """Unordered match for parallel calls; error taxonomy follows the evaluation guide."""
    answer, closed = split_thinking(raw_output, thinking_enabled)
    if closed is False:
        return dict(correct=False, error='unclosed_thinking', fmt='none', n_calls=0, thinking_closed=False)
    calls, fmt = parse_tool_calls(answer, tools)
    base = dict(fmt=fmt, n_calls=len(calls), thinking_closed=closed,
                calls=[dict(name=n, args=a) for n, a in calls])
    if fmt == 'error':
        return dict(base, correct=False, error='parse_error')
    if not calls:
        return dict(base, correct=False, error='no_tool_call')
    if len(calls) != len(gold_calls):
        return dict(base, correct=False, error='wrong_call_count')
    if _assign(calls, list(gold_calls), tools):
        return dict(base, correct=True, error=None)
    gold_names = sorted(next(iter(g)) for g in gold_calls)
    if sorted(n for n, _ in calls) != gold_names:
        return dict(base, correct=False, error='wrong_function')
    return dict(base, correct=False, error='wrong_arguments')


def render_call_xml(name, args):
    """Render one call in the chat template's own format (used by oracle tests)."""
    def text(value):
        if isinstance(value, bool):
            return 'true' if value else 'false'
        return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    body = ''.join(f'<parameter={k}>\n{text(v)}\n</parameter>\n' for k, v in args.items())
    return f'<tool_call>\n<function={name}>\n{body}</function>\n</tool_call>'


def _self_test():
    D = Decimal
    cases = [
        ('Adım 1...\nFinal answer: 18', 'en', D(18), 'marker'),
        ('**Final answer: $1,450,000**', 'en', D(1450000), 'marker'),
        ('Nihai cevap: 1.450.000 TL', 'tr', D(1450000), 'marker'),
        ('NİHAİ CEVAP: 42', 'tr', D(42), 'marker'),
        ('Nihai cevap: 3,5', 'tr', D('3.5'), 'marker'),
        ('Nihai cevap: 1,450,000', 'tr', D(1450000), 'marker'),
        ('Final answer: 1.5', 'en', D('1.5'), 'marker'),
        ('Final answer:\n7', 'en', D(7), 'marker'),
        ('Sonuç \\boxed{216}.', 'tr', D(216), 'boxed'),
        ('Toplam 9 * 2 = 18 dolar eder.', 'tr', D(18), 'fallback'),
        ('Final answer: -4', 'en', D(-4), 'marker'),
        ('Final answer: 12. Then 99 extra', 'en', D(12), 'marker'),
    ]
    for text, lang, want, method in cases:
        got = extract_final_number(text, lang)
        assert got == (want, method), (text, got, want, method)
    assert extract_final_number('no digits here', 'en') == (None, 'none')
    assert parse_number('1.450', 'tr') == D(1450) and parse_number('1.450', 'en') == D('1.450')
    assert parse_number('1,450', 'tr') == D('1.45') and parse_number('1,450', 'en') == D(1450)
    assert parse_number('1.450.000', 'en') is None
    # thinking handling
    assert split_thinking('reason 1</think>Final answer: 5<|im_end|>', True) == ('Final answer: 5', True)
    assert split_thinking('never closes', True) == ('', False)
    assert split_thinking('Final answer: 5<|im_end|>', False) == ('Final answer: 5', None)
    assert score_math('x</think>Final answer: 18', 18, 'en', True)['correct_strict']
    assert not score_math('x</think>so 18 apples', 18, 'en', True)['correct_strict']
    assert score_math('x</think>so 18 apples', 18, 'en', True)['correct_any']
    assert score_math('still thinking', 18, 'en', True)['method'] == 'unclosed_thinking'
    s = score_symbolic('104<|im_end|>', 104, 'en', False)
    assert s['correct'] and s['number_only']
    s = score_symbolic('(54+38)*3-17 = 259', 259, 'tr', False)
    assert s['correct'] and not s['number_only']
    s = score_symbolic('**575**.', 575, 'tr', False)
    assert s['correct'] and s['number_only']
    assert not score_symbolic('105', 104, 'en', False)['correct']
    tools = [dict(name='calc', parameters=dict(type='object', required=['base', 'height'],
             properties=dict(base=dict(type='integer'), height=dict(type='integer'), unit=dict(type='string'))))]
    gold = [dict(calc=dict(base=[10], height=[5], unit=['units', '']))]
    xml = '</think>' + render_call_xml('calc', dict(base=10, height=5))
    assert score_toolcall(xml, gold, tools, True)['correct']
    assert score_toolcall(xml.replace('\n5\n', '\n6\n'), gold, tools, True)['error'] == 'wrong_arguments'
    assert score_toolcall(xml.replace('calc', 'other'), gold, tools, True)['error'] in ('wrong_function', 'parse_error')
    assert score_toolcall('</think>I can help with that.', gold, tools, True)['error'] == 'no_tool_call'
    js = '</think><tool_call>{"name": "calc", "arguments": {"base": 10, "height": 5, "unit": "Units"}}</tool_call>'
    assert score_toolcall(js, gold, tools, True)['correct']
    two = xml + render_call_xml('calc', dict(base=1, height=2))
    assert score_toolcall(two, gold, tools, True)['error'] == 'wrong_call_count'
    print('self-test passed', SCORER_VERSION)


if __name__ == '__main__':
    if '--self-test' in sys.argv:
        _self_test()
    else:
        sys.exit('Usage: lfm3_eval_v2_scoring.py --self-test')
