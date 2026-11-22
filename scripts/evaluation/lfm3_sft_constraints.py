"""Small checkers for explicit constraints in Turkish prompts (SFT core v01, Atlas-derived rows).

parse_constraints(prompt) -> list of dicts; check_constraints(items, answer) -> (ok, failures).
Only constraints that can be counted are parsed: word limits, bullet counts, sentence limits, JSON-only output. The parser is
deliberately conservative (a prompt whose constraint is not recognised simply has no automatic constraint check).
"""
import json
import re

WORD = re.compile(r"[\wçğıöşüÇĞİÖŞÜ'’-]+")
BULLET = re.compile(r'^\s*(?:[-*•]|\d+[.)])\s+\S')


def parse_constraints(prompt):
    items = []
    for m in re.finditer(r'en (?:fazla|çok) (\d+) kelime', prompt, re.I):
        items.append(dict(type='max_words', n=int(m.group(1))))
    for m in re.finditer(r'en az (\d+) kelime', prompt, re.I):
        items.append(dict(type='min_words', n=int(m.group(1))))
    for m in re.finditer(r'tam olarak (\d+) madde|(\d+) maddelik|(\d+) maddeden oluşan', prompt, re.I):
        items.append(dict(type='bullets', n=int(next(g for g in m.groups() if g))))
    for m in re.finditer(r'en fazla (\d+) madde', prompt, re.I):
        items.append(dict(type='max_bullets', n=int(m.group(1))))
    if re.search(r'\btek (?:bir )?cümle', prompt, re.I):
        items.append(dict(type='max_sentences', n=1))
    for m in re.finditer(r'en fazla (\d+) cümle', prompt, re.I):
        items.append(dict(type='max_sentences', n=int(m.group(1))))
    if re.search(r'json', prompt, re.I) and re.search(r'(?:yalnızca|sadece|yalnız)\b.{0,40}json|json.{0,30}(?:döndür|ver\b|üret)',
                                                      prompt, re.I | re.S):
        items.append(dict(type='json'))
    seen, unique = set(), []
    for item in items:
        key = json.dumps(item, sort_keys=True)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def count_words(text):
    return len(WORD.findall(text))


def count_bullets(text):
    return sum(1 for line in text.split('\n') if BULLET.match(line))


def count_sentences(text):
    parts = [p for p in re.split(r'(?<=[.!?])\s+', text.strip()) if p.strip()]
    return len(parts)


def strip_fence(text):
    match = re.match(r'^\s*```(?:json)?\s*\n(.*?)\n?```\s*$', text, re.S | re.I)
    return match.group(1) if match else text


def check_constraints(items, answer):
    failures = []
    if not answer.strip():
        return False, ['empty']
    for item in items:
        kind, n = item['type'], item.get('n')
        if kind == 'max_words' and count_words(answer) > n:
            failures.append(f'max_words {count_words(answer)}>{n}')
        elif kind == 'min_words' and count_words(answer) < n:
            failures.append(f'min_words {count_words(answer)}<{n}')
        elif kind == 'bullets' and count_bullets(answer) != n:
            failures.append(f'bullets {count_bullets(answer)}!={n}')
        elif kind == 'max_bullets' and count_bullets(answer) > n:
            failures.append(f'max_bullets {count_bullets(answer)}>{n}')
        elif kind == 'max_sentences' and count_sentences(answer) > n:
            failures.append(f'max_sentences {count_sentences(answer)}>{n}')
        elif kind == 'json':
            try:
                json.loads(strip_fence(answer))
            except ValueError:
                failures.append('json invalid')
    return not failures, failures


def _self_test():
    assert parse_constraints('Özetle, en fazla 100 kelime olsun. Tam olarak 2 madde ver. Yalnızca geçerli JSON döndür.') == [
        dict(type='max_words', n=100), dict(type='bullets', n=2), dict(type='json')]
    assert parse_constraints('Tek bir cümle yaz.') == [dict(type='max_sentences', n=1)]
    assert check_constraints([dict(type='bullets', n=2)], '- bir\n- iki')[0]
    assert not check_constraints([dict(type='bullets', n=3)], '- bir\n- iki')[0]
    assert check_constraints([dict(type='json')], '```json\n{"a": 1}\n```')[0]
    assert not check_constraints([dict(type='max_words', n=2)], 'bir iki üç')[0]
    assert check_constraints([dict(type='max_sentences', n=1)], 'Bu bir cümledir.')[0]
    assert not check_constraints([dict(type='max_sentences', n=1)], 'Bir. İki.')[0]
    print('self-test ok')


if __name__ == '__main__':
    _self_test()
