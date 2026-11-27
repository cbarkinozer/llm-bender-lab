"""Code checks for the exp-006 Turkish DPO pairs and the primary metric (no model judge anywhere).

  from tr_dpo6_checks import check_answer
  result = check_answer(items, answer, prompt_text=..., ended=True, grounded=False)
  result.ok -> every check passed; result.failures -> list of short reasons

Constraint items (dicts, `type` plus fields). The first five come from lfm3_sft_constraints (word, bullet, sentence limits, JSON):
  max_words n, min_words n, bullets n, max_bullets n, max_sentences n, json
  exact_sentences n          exactly n sentences
  must_include word          the word appears (Turkish case-folded, whole word or its suffixed form: prefix match)
  must_not_include word      the word does not appear (same matching)
  no_greeting                the answer does not open with a greeting or a filler opener
  no_closing_question        the last sentence is not a question
Always checked: the answer is not empty, ended normally (`ended`), is Turkish (small English-stopword share), has no repetition loop.
With grounded=True: every number in the answer also occurs in `prompt_text` (the source plus the instruction).

`python tr_dpo6_checks.py` runs the self-test (hand-made pass and fail cases for every check).
"""
import re
import sys
from collections import namedtuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lfm3_sft_constraints as base  # noqa: E402

Result = namedtuple('Result', 'ok failures')

NUMBER = re.compile(r'\d+(?:[.,]\d+)*')
LIST_MARKER = re.compile(r'^\s*\d+[.)]\s+', re.M)
GREETING = re.compile(r'^\W*(merhaba|selam|selamlar|sevgili|değerli|günaydın|iyi günler|elbette|tabii( ki)?|tabi|şüphesiz|'
                      r'memnuniyetle|harika bir soru|güzel bir soru|tamam)\b', re.I)
ENGLISH_STOP = {'the', 'and', 'of', 'to', 'is', 'in', 'that', 'it', 'for', 'with', 'as', 'was', 'on', 'are', 'this', 'be', 'by',
                'an', 'or', 'which', 'from', 'at', 'not', 'have', 'has', 'you', 'your', 'can', 'will'}


def tr_lower(text):
    return text.replace('İ', 'i').replace('I', 'ı').lower()


def tr_words(text):
    return base.WORD.findall(tr_lower(text))


def has_word(text, word):
    """True when a word of the text starts with the case-folded `word` (so suffixed forms count)."""
    stem = tr_lower(word)
    return any(w.startswith(stem) for w in tr_words(text))


def numbers_in(text):
    return set(NUMBER.findall(LIST_MARKER.sub('', text)))


def number_variants(token):
    digits = re.sub(r'[.,]', '', token)
    return {token, token.replace('.', ','), token.replace(',', '.'), digits}


def invented_numbers(source_text, answer):
    allowed = set()
    for token in numbers_in(source_text):
        allowed |= number_variants(token)
    return sorted(token for token in numbers_in(answer) if not (number_variants(token) & allowed))


def english_share(text):
    ws = [w for w in re.findall(r"[A-Za-zçğıöşüÇĞİÖŞÜ']+", text)]
    return (sum(w.lower() in ENGLISH_STOP for w in ws) / len(ws)) if ws else 0.0


def has_loop(text, n=6, repeats=3):
    ws = tr_words(text)
    seen = {}
    for i in range(len(ws) - n + 1):
        gram = tuple(ws[i:i + n])
        seen[gram] = seen.get(gram, 0) + 1
        if seen[gram] >= repeats:
            return True
    return False


def last_sentence(text):
    parts = [p for p in re.split(r'(?<=[.!?…])\s+', text.strip()) if re.search(r'\w', p)]
    return parts[-1] if parts else ''


def check_answer(items, answer, prompt_text='', ended=True, grounded=False):
    failures = []
    if not ended:
        failures.append('not ended')
    _, base_failures = base.check_constraints([i for i in items if i['type'] in
                                                {'max_words', 'min_words', 'bullets', 'max_bullets', 'max_sentences', 'json'}], answer)
    failures += base_failures
    if not answer.strip():
        return Result(False, failures)
    for item in items:
        kind = item['type']
        if kind == 'exact_sentences' and base.count_sentences(answer) != item['n']:
            failures.append(f"exact_sentences {base.count_sentences(answer)}!={item['n']}")
        elif kind == 'must_include' and not has_word(answer, item['word']):
            failures.append(f"must_include {item['word']}")
        elif kind == 'must_not_include' and has_word(answer, item['word']):
            failures.append(f"must_not_include {item['word']}")
        elif kind == 'no_greeting' and GREETING.match(answer.strip()):
            failures.append('greeting')
        elif kind == 'no_closing_question' and last_sentence(answer).rstrip('*_ )"”').endswith('?'):
            failures.append('closing question')
    if english_share(answer) > 0.12:
        failures.append('english')
    if has_loop(answer):
        failures.append('loop')
    if grounded:
        invented = invented_numbers(prompt_text, answer)
        if invented:
            failures.append('invented numbers ' + ','.join(invented[:3]))
    return Result(not failures, failures)


def _self_test():
    tr = 'Bu bir deneme metnidir. Sabırlı olmak önemlidir.'
    assert check_answer([dict(type='max_words', n=20)], tr).ok
    assert not check_answer([dict(type='max_words', n=3)], tr).ok
    assert not check_answer([], tr, ended=False).ok
    assert not check_answer([], '   ').ok
    assert check_answer([dict(type='exact_sentences', n=2)], tr).ok
    assert not check_answer([dict(type='exact_sentences', n=3)], tr).ok
    assert check_answer([dict(type='must_include', word='sabır')], tr).ok  # suffixed form: sabırlı
    assert check_answer([dict(type='must_include', word='SABIR')], tr).ok  # Turkish case folding
    assert not check_answer([dict(type='must_include', word='cesaret')], tr).ok
    assert not check_answer([dict(type='must_not_include', word='deneme')], tr).ok
    assert check_answer([dict(type='must_not_include', word='cesaret')], tr).ok
    assert not check_answer([dict(type='no_greeting')], 'Merhaba! İşte özet.').ok
    assert not check_answer([dict(type='no_greeting')], 'Elbette, işte özet.').ok
    assert check_answer([dict(type='no_greeting')], 'Özet: konu kısaca şudur.').ok
    assert not check_answer([dict(type='no_closing_question')], 'Özet budur. Başka bir şey ister misin?').ok
    assert check_answer([dict(type='no_closing_question')], 'Özet budur. Soru işareti yok.').ok
    assert check_answer([dict(type='bullets', n=2)], '- bir\n- iki').ok
    assert not check_answer([dict(type='bullets', n=3)], '- bir\n- iki').ok
    assert not check_answer([], 'The cat is on the mat and it is not in the box for you').ok  # English reply
    assert not check_answer([], 'bir iki üç dört beş altı ' * 4).ok  # loop
    src = 'Şirket 2023 yılında 1.250 çalışan ve %12 büyüme bildirdi.'
    assert check_answer([], 'Şirket 2023 yılında 1.250 kişi çalıştırdı.', prompt_text=src, grounded=True).ok
    assert check_answer([], 'Büyüme %12 oldu, çalışan sayısı 1250.', prompt_text=src, grounded=True).ok  # separator variant
    assert not check_answer([], 'Şirket 2023 yılında 1.400 çalışana ulaştı.', prompt_text=src, grounded=True).ok  # invented
    assert check_answer([], 'Şirket 2023 yılında 1.400 çalışana ulaştı.', prompt_text=src, grounded=False).ok  # not grounded
    assert check_answer([], '1. Birinci madde 2023.\n2. İkinci madde.', prompt_text=src, grounded=True).ok  # list markers are not numbers
    assert tr_lower('IŞIK İNCE') == 'ışık ince'
    print('self-test ok')


if __name__ == '__main__':
    _self_test()
