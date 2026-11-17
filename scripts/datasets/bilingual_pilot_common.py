"""Shared constants/helpers for the four-direction bilingual pilot (train builder + frozen eval)."""
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/turkish-capability/lfm3-1.7b'
PILOT = BASE / 'bilingual-pilot-v01'

DIRECTIONS = ['tr-tr', 'en-tr', 'tr-en', 'en-en']  # input language - output language

# The reviewed system prompt is shared by all 160 originals (asserted by the builder).
SYSTEM_TR = ('Sen doğru, yardımsever ve güvenilir bir Türkçe asistansın. Kullanıcının istediği biçime ve kısıtlara uy. '
             'Yanıtın ayrıntısını sorunun gerektirdiği düzeye göre ayarla. Belirsizliği belirt; eksik bilgiyi uydurma.')
# Deliberately drops "Turkish" (the role names the working language; EN rows state output language explicitly).
SYSTEM_EN = ('You are an accurate, helpful and reliable assistant. Follow the format and constraints the user requests. '
             'Adjust the level of detail to what the question requires. State uncertainty; do not invent missing information.')
SYSTEM = {'tr': SYSTEM_TR, 'en': SYSTEM_EN}

# Output-language instruction, written in the INPUT language, appended to the user turn.
INSTRUCTION = {
    ('tr', 'tr'): 'Yanıtını Türkçe ver.',
    ('tr', 'en'): 'Yanıtını İngilizce ver.',
    ('en', 'tr'): 'Answer in Turkish.',
    ('en', 'en'): 'Answer in English.',
}

# Training-only EN-output variants for groups whose task requires keeping Turkish object text (see DATA-CHANGES.md).
PRESERVE_EXPLAIN_GROUPS = {'g004', 'g007', 'g012', 'g015', 'g019', 'g130'}   # Turkish text kept, explanations translated
PRESERVE_ANSWER_GROUPS = {'g041', 'g051', 'g052', 'g055', 'g123', 'g135'}    # answer is the requested Turkish text itself
NEUTRAL_CONTENT_GROUPS = {'g010', 'g044', 'g058'}                            # JSON / name answers; standard instruction kept
INSTRUCTION_PRESERVE_EXPLAIN = {('tr', 'en'): 'İngilizce açıkla; istenen Türkçe metni olduğu gibi koru.',
                                ('en', 'en'): 'Explain in English; preserve the requested Turkish text.'}
INSTRUCTION_PRESERVE_ANSWER = {('tr', 'en'): 'Yanıtını İngilizce ver; istenen Türkçe metni olduğu gibi koru.',
                               ('en', 'en'): 'Answer in English; preserve the requested Turkish text.'}


def instruction_for(group_key, src, dst):
    """(variant, text) for a training row; group_key like 'g041'. EN-output only is ever varied."""
    if dst == 'en' and group_key in PRESERVE_EXPLAIN_GROUPS:
        return 'preserve_explain', INSTRUCTION_PRESERVE_EXPLAIN[(src, dst)]
    if dst == 'en' and group_key in PRESERVE_ANSWER_GROUPS:
        return 'preserve_answer', INSTRUCTION_PRESERVE_ANSWER[(src, dst)]
    return 'standard', INSTRUCTION[(src, dst)]


def all_instruction_texts():
    return list(INSTRUCTION.values()) + list(INSTRUCTION_PRESERVE_EXPLAIN.values()) + list(INSTRUCTION_PRESERVE_ANSWER.values())


def instruction_separator(user):
    """Newlines needed so the instruction always lands after a blank line, without altering the original text."""
    trailing = len(user) - len(user.rstrip('\n'))
    return '\n' * max(0, 2 - trailing)


def with_instruction(user, in_lang, out_lang, text=None):
    text = text or INSTRUCTION[(in_lang, out_lang)]
    return user + instruction_separator(user) + text


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def sha256_text(text):
    return sha256_bytes(text.encode('utf-8'))


def jsonl_bytes(rows):
    return ''.join(json.dumps(r, ensure_ascii=False, sort_keys=False) + '\n' for r in rows).encode('utf-8')


def json_bytes(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def freeze(path, data):
    """Write once; on rerun the file must match byte for byte (frozen artifacts never drift silently)."""
    path = Path(path)
    if path.exists():
        assert path.read_bytes() == data, f'Frozen artifact differs: {path}'
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def read_jsonl(path):
    return [json.loads(l) for l in Path(path).read_text(encoding='utf-8').splitlines() if l.strip()]


def normalized(text):
    return ' '.join(re.findall(r'\w+', unicodedata.normalize('NFKC', text).casefold()))


def parse_translation_file(path):
    """Parse translations/part-NNN.txt -> {group_key: dict(source_id, user, assistant, reasoning, flags)}."""
    out, cur, field = {}, None, None
    for raw in Path(path).read_text(encoding='utf-8').split('\n'):
        if raw.startswith('=== '):
            cur = raw[4:].strip()
            assert re.fullmatch(r'g\d{3}', cur) and cur not in out, f'bad/duplicate group header {raw!r}'
            out[cur] = dict(source_id=None, user=[], assistant=[], reasoning=None, flags=[])
            field = None
        elif raw.startswith('@@SOURCE_ID '):
            out[cur]['source_id'] = raw[len('@@SOURCE_ID '):].strip()
            field = None
        elif raw in ('@@USER', '@@ASSISTANT', '@@REASONING', '@@FLAGS'):
            field = raw[2:].lower()
            if field == 'reasoning':
                out[cur]['reasoning'] = []
        elif field is not None:
            out[cur][field].append(raw)
    for key, entry in out.items():
        for f in ('user', 'assistant'):
            entry[f] = '\n'.join(entry[f]).strip('\n')
            assert entry[f], f'{key}: empty {f}'
        if entry['reasoning'] is not None:
            entry['reasoning'] = '\n'.join(entry['reasoning']).strip('\n')
            assert entry['reasoning'], f'{key}: empty reasoning'
        flags = []
        for line in entry['flags']:
            if line.strip():
                parts = [p.strip() for p in line.split('|', 2)]
                assert len(parts) == 3 and parts[0] in ('info', 'low', 'medium', 'high'), f'{key}: bad flag {line!r}'
                flags.append(dict(severity=parts[0], type=parts[1], note=parts[2]))
        entry['flags'] = flags
    return out
