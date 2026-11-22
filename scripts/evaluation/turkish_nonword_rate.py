"""Share of word types a Turkish morphological analyzer (Zeyrek) cannot analyze: a proxy for invented words.

  python turkish_nonword_rate.py text FILE_OR_DASH [--show N]    plain text, one rate
  python turkish_nonword_rate.py jsonl FILE --field FIELD        one rate per row plus the pooled rate
Needs `pip install zeyrek` (run it in a venv). The analyzer misses some real words (names, loanwords), so the rate is only
meaningful next to the same measure on human Turkish text (calibration), never as an absolute quality score.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

WORD = re.compile(r"[a-zçğıöşüâîûA-ZÇĞİÖŞÜÂÎÛ]+(?:['’][a-zçğıöşüâîû]+)?")
CODE = re.compile(r'```.*?```|`[^`\n]*`', re.S)


def tokens(text):
    """Lowercased alphabetic word forms of 3+ letters outside code; apostrophe names (Ali'nin) are dropped."""
    out = []
    for w in WORD.findall(CODE.sub(' ', text)):
        if "'" in w or '’' in w or len(w) < 3 or (w.isupper() and len(w) <= 5):
            continue
        out.append(w.replace('İ', 'i').replace('I', 'ı').lower())
    return out


class Analyzer:
    """Zeyrek loses analyses for some stems after many calls (a stale analyzer returned Unk for 'edilir', 'olarak'),
    so every Unk is re-checked on a fresh analyzer that is rebuilt every RECHECK_LIFETIME checks."""
    RECHECK_LIFETIME = 25

    def __init__(self):
        import zeyrek
        self.zeyrek, self.cache = zeyrek, {}
        self.main, self.checker, self.checker_uses = zeyrek.MorphAnalyzer(), None, 0

    @staticmethod
    def analyzed(analyzer, word):
        return any(r.lemma != 'Unk' for r in analyzer.analyze(word)[0])

    def known(self, word):
        if word not in self.cache:
            ok = self.analyzed(self.main, word)
            if not ok:
                if self.checker is None or self.checker_uses >= self.RECHECK_LIFETIME:
                    self.checker, self.checker_uses = self.zeyrek.MorphAnalyzer(), 0
                self.checker_uses += 1
                ok = self.analyzed(self.checker, word)
            self.cache[word] = ok
        return self.cache[word]

    @staticmethod
    def is_english(word):
        """English words inside Turkish text are code-switching, not invented words (needs `pip install wordfreq`)."""
        try:
            from wordfreq import zipf_frequency
        except ImportError:
            return False
        return zipf_frequency(word, 'en') >= 2.5 and zipf_frequency(word, 'en') > zipf_frequency(word, 'tr')

    def rate(self, words):
        types = Counter(words)
        unknown = Counter({w: c for w, c in types.items() if not self.known(w)})
        english = Counter({w: c for w, c in unknown.items() if self.is_english(w)})
        candidates = unknown - english
        total = max(1, sum(types.values()))
        return dict(tokens=sum(types.values()), unknown_tokens=sum(unknown.values()),
                    token_rate=round(sum(unknown.values()) / total, 4),
                    english_token_rate=round(sum(english.values()) / total, 4),
                    candidate_token_rate=round(sum(candidates.values()) / total, 4),
                    types=len(types), unknown_types=len(unknown),
                    type_rate=round(len(unknown) / max(1, len(types)), 4),
                    top_candidates=candidates.most_common(15), top_unknown=unknown.most_common(15))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='cmd', required=True)
    t = sub.add_parser('text')
    t.add_argument('file')
    t = sub.add_parser('jsonl')
    t.add_argument('file')
    t.add_argument('--field', required=True)
    args = parser.parse_args()
    analyzer = Analyzer()
    if args.cmd == 'text':
        text = sys.stdin.read() if args.file == '-' else Path(args.file).read_text(encoding='utf-8')
        print(json.dumps(analyzer.rate(tokens(text)), ensure_ascii=False))
    else:
        rows = [json.loads(x) for x in Path(args.file).read_text(encoding='utf-8').splitlines()]
        words = [w for r in rows for w in tokens(r[args.field])]
        print(json.dumps(analyzer.rate(words), ensure_ascii=False))


if __name__ == '__main__':
    main()
