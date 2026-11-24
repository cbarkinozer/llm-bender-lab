"""Scoring of tool calls for the LiquidAI/phone-assistant-tools dataset (Apache-2.0 data, own implementation).

A prediction is correct when it makes exactly the gold calls, in any order. Arguments are compared by the kind that the dataset's
scoring.json gives for each argument of each tool: numbers, booleans and enums exactly; dates and times as values; codes without
spaces and dashes; names without case, accents and word order; free text with a similarity tolerance. Optional arguments left at
their schema default count as absent.

This is a re-implementation from the dataset's description, so its numbers can differ slightly from other scorers for the same data.
"""
import ast
import itertools
import math
import operator
import re
import unicodedata
from collections import Counter
from datetime import date, datetime, time
from difflib import SequenceMatcher

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
       ast.Mod: operator.mod, ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}
TIME = re.compile(r'(\d{1,2}):(\d{2})(?::(\d{2}))?')
DATE = re.compile(r'\d{4}-\d{2}-\d{2}')
DATETIME = re.compile(r'\d{4}-\d{2}-\d{2}[T ]\d{1,2}:\d{2}(?::\d{2})?')


def fold(text):
    """Case-, accent- and punctuation-insensitive form of a string."""
    t = unicodedata.normalize('NFKD', str(text)).casefold()
    t = ''.join(c for c in t if not unicodedata.combining(c))
    t = ''.join(' ' if unicodedata.category(c)[0] in 'PSZ' else c for c in t)
    return ' '.join(t.split())


def contained(a, b):
    short, long = sorted((a, b), key=len)
    return bool(short) and short in long and len(short) >= 0.5 * len(long)


def same_name(a, b):
    a, b = fold(a), fold(b)
    return a == b or sorted(a.split()) == sorted(b.split()) or contained(a, b)


def same_text(a, b):
    a, b = fold(a), fold(b)
    return a == b or contained(a, b) or (bool(a) and bool(b) and SequenceMatcher(None, a, b).ratio() >= 0.6)


def when(value, kind):
    """Parse a date, time or datetime string, or None when it does not have the expected format."""
    s = str(value).strip()
    try:
        if kind == 'date':
            return date.fromisoformat(s) if DATE.fullmatch(s) else None
        if kind == 'time':
            m = TIME.fullmatch(s)
            return time(int(m[1]), int(m[2]), int(m[3] or 0)) if m else None
        if kind == 'datetime':
            return datetime.fromisoformat(s.replace(' ', 'T')) if DATETIME.fullmatch(s) else None
    except ValueError:
        return None
    return None


def arithmetic(expression):
    """Value of a plain arithmetic expression, or None."""
    def walk(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            left, right = walk(node.left), walk(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError('exponent too large')
            return OPS[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
            return OPS[type(node.op)](walk(node.operand))
        raise ValueError('unsupported expression')
    text = str(expression).replace('^', '**').replace('×', '*').replace('÷', '/')
    try:
        return float(walk(ast.parse(text, mode='eval').body))
    except (SyntaxError, ValueError, TypeError, OverflowError, ZeroDivisionError, RecursionError):
        return None


def same_expr(gold, pred):
    g, p = arithmetic(gold), arithmetic(pred)
    return g is not None and p is not None and math.isclose(g, p, rel_tol=1e-9, abs_tol=1e-9)


def same_list(gold, pred, equal):
    return (isinstance(pred, list) and len(gold) == len(pred)
            and any(all(equal(g, p) for g, p in zip(gold, perm)) for perm in itertools.permutations(pred)))


def strip_code(value):
    return re.sub(r'[\s\-().]', '', str(value).casefold())


COMPARE = {
    'bool': lambda g, p: isinstance(p, bool) and g == p,
    'int': lambda g, p: isinstance(p, (int, float)) and not isinstance(p, bool) and abs(float(g) - float(p)) < 1e-6,
    'number': lambda g, p: isinstance(p, (int, float)) and not isinstance(p, bool) and abs(float(g) - float(p)) < 1e-6,
    'enum': lambda g, p: isinstance(p, str) and str(g).strip().lower() == p.strip().lower(),
    'code': lambda g, p: isinstance(p, (str, int)) and not isinstance(p, bool) and strip_code(g) == strip_code(p),
    'date': lambda g, p: when(p, 'date') is not None and when(p, 'date') == when(g, 'date'),
    'time': lambda g, p: when(p, 'time') is not None and when(p, 'time') == when(g, 'time'),
    'datetime': lambda g, p: when(p, 'datetime') is not None and when(p, 'datetime') == when(g, 'datetime'),
    'expr': same_expr,
    'name': lambda g, p: isinstance(p, str) and same_name(g, p),
    'text': lambda g, p: isinstance(p, str) and same_text(g, p),
    'list_enum': lambda g, p: isinstance(p, list) and sorted(str(x).lower() for x in g) == sorted(str(x).lower() for x in p),
    'list_name': lambda g, p: same_list(g, p, same_name),
    'list_text': lambda g, p: same_list(g, p, same_text),
}


class Scorer:
    def __init__(self, tools, kinds):
        self.schemas = {t['function']['name']: t['function']['parameters'] for t in tools}
        self.kinds = kinds
        for name, schema in self.schemas.items():
            missing = set(schema.get('properties', {})) - set(kinds.get(name, {}))
            assert not missing, f'{name}: no scoring kind for {sorted(missing)}'
        unknown = {k for tool in kinds.values() for k in tool.values()} - set(COMPARE)
        assert not unknown, f'unknown scoring kinds {sorted(unknown)}'

    def canonical(self, name, arguments):
        """Fill schema defaults, drop empty optional values, and treat end_date == date as a single day."""
        schema = self.schemas[name]
        required = set(schema.get('required', []))
        out = {k: v for k, v in (arguments or {}).items() if k in required or v not in (None, '', [])}
        for key, prop in schema.get('properties', {}).items():
            if key not in out and 'default' in prop:
                out[key] = prop['default']
        if 'end_date' in out and out.get('end_date') == out.get('date'):
            del out['end_date']
        return out

    def same_call(self, gold, pred):
        name = gold['name']
        if name != pred.get('name') or name not in self.schemas:
            return False
        g, p = self.canonical(name, gold.get('arguments')), self.canonical(name, pred.get('arguments'))
        if set(g) != set(p):
            return False
        try:
            return all(COMPARE[self.kinds[name][k]](g[k], p[k]) for k in g)
        except (TypeError, ValueError, OverflowError):
            return False

    def calls_match(self, gold, pred):
        """True when the prediction makes exactly the gold calls, in any order (an empty gold needs an empty prediction)."""
        if len(gold) != len(pred) or any(c.get('name') not in self.schemas for c in pred):
            return False
        return any(all(self.same_call(g, p) for g, p in zip(gold, perm)) for perm in itertools.permutations(pred))

    @staticmethod
    def name_f1(gold, pred):
        """F1 of the multisets of tool names (partial credit for picking the right tools)."""
        g, p = Counter(c['name'] for c in gold), Counter(c.get('name') for c in pred)
        overlap = sum((g & p).values())
        return 0.0 if overlap == 0 else 2 * overlap / (sum(g.values()) + sum(p.values()))
