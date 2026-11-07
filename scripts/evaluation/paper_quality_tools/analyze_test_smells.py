"""Frozen measurement-only extraction; see provenance.json. No benchmark samples."""
from __future__ import annotations
"""
Test Code Smell Analysis for SLM-Generated Unit Tests

Detects 8 classic test smells using static AST analysis:
  1. Assertion Roulette     - multiple asserts, none with failure messages
  2. Eager Test             - SUT function called more than once in a single test
  3. Mystery Guest          - test uses external resources (files, network, DB)
  4. Magic Number Test      - unexplained numeric literals in assertions
  5. Obscure Test           - test function too long or too many local variables
  6. General Fixture        - setUp / @pytest.fixture creates ≥3 objects
  7. Conditional Test Logic - if / for / while / try inside test body
  8. Fragile Test           - time.sleep, datetime.now(), unseeded random, hardcoded paths

Literature references:
  van Deursen et al. (2001) "Refactoring Test Code"
  Palomba et al. (2018) "Automatic Test Smell Detection"

Usage:
    python analyze_test_smells.py [--output-dir OUTPUT_DIR]
                                  [--dataset {initial,temperature,realworld,all}]
"""
import ast
import json
import re
import argparse
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
DEFAULT_BASE_DIR = Path(__file__).parent.parent
PREFIXES = ['linecov', 'linecov2']

def _classify_dataset(dir_name: str) -> str:
    """Map a predictions_* directory name to a logical dataset label."""
    if 'realworld' in dir_name:
        return 'realworld'
    if 'temperature' in dir_name:
        return 'temperature'
    if 'initial' in dir_name:
        return 'initial'
    return dir_name

def discover_prediction_files(base_dir: Path, target_datasets=None):
    """
    Yield (dataset_label, run_label, model, temperature, approach, jsonl_path) tuples
    by scanning all TestEval/predictions_*/run_*/ directories.

    File naming convention: {prefix}_{model}_temp_{temp}.jsonl
    Approach is "One-Step" (linecov_) or "Two-Step" (linecov2_).
    """
    testeval_dir = base_dir / 'TestEval'
    if not testeval_dir.exists():
        return
    for pred_dir in sorted(testeval_dir.glob('predictions_*')):
        if not pred_dir.is_dir():
            continue
        if 'judgellm' in pred_dir.name:
            continue
        name = pred_dir.name
        if re.search('_(initial|realworld)_\\d+$', name):
            if not re.search('_(initial|realworld)_1$', name):
                continue
        dataset = _classify_dataset(pred_dir.name)
        if target_datasets and dataset not in target_datasets:
            continue
        for run_dir in sorted(pred_dir.glob('run_*')):
            if not run_dir.is_dir():
                continue
            run_label = run_dir.name
            for jsonl_path in sorted(run_dir.glob('*.jsonl')):
                stem = jsonl_path.stem
                if 'pynguin' in stem:
                    continue
                m = re.match('^(linecov2?_)(.+)_temp_(\\d+\\.\\d+)$', stem)
                if not m:
                    continue
                prefix_str = m.group(1).rstrip('_')
                approach = 'Two-Step' if prefix_str == 'linecov2' else 'One-Step'
                model = m.group(2)
                temperature = m.group(3)
                yield (dataset, run_label, model, temperature, approach, jsonl_path)
SMELL_NAMES = ['assertion_roulette', 'eager_test', 'mystery_guest', 'magic_number_test', 'obscure_test', 'general_fixture', 'conditional_test_logic', 'fragile_test', 'unknown_test', 'trivial_assertion', 'duplicated_setup']
SMELL_LABELS = {'assertion_roulette': 'Assertion\nRoulette', 'eager_test': 'Eager\nTest', 'mystery_guest': 'Mystery\nGuest', 'magic_number_test': 'Magic\nNumber Test', 'obscure_test': 'Obscure\nTest', 'general_fixture': 'Lack of\nCohesion', 'conditional_test_logic': 'Conditional\nTest Logic', 'fragile_test': 'External\nDependency', 'unknown_test': 'Unverified\nAction', 'trivial_assertion': 'Trivial\nAssertion', 'duplicated_setup': 'Duplicated\nSetup'}
MYSTERY_GUEST_BASE_MODULES = {'requests', 'httpx', 'socket', 'ftplib', 'aiohttp', 'sqlite3', 'sqlalchemy', 'pymongo', 'psycopg2', 'pymysql', 'motor', 'subprocess', 'boto3', 'google', 'azure'}
MYSTERY_GUEST_FULL_MODULES = {'urllib.request', 'urllib.robotparser', 'http.client', 'http.server'}
MYSTERY_GUEST_FS_CALLS = {'listdir', 'scandir', 'remove', 'unlink', 'rmdir', 'makedirs', 'mkdir', 'rename', 'stat', 'lstat', 'access', 'read_text', 'read_bytes', 'write_text', 'write_bytes', 'iterdir', 'glob', 'rglob', 'rmtree', 'copytree', 'copyfile', 'copy2', 'mkstemp', 'mkdtemp', 'NamedTemporaryFile', 'TemporaryFile', 'TemporaryDirectory', 'open'}
EXEMPT_NUMBERS = {0, 0.0, 1, -1, 2, -2}

@dataclass
class SmellRecord:
    """Analysis result for a single (prediction, target_line) pair."""
    dataset: str
    model: str
    temperature: str
    approach: str
    run: str
    task_num: str
    task_title: str
    func_name: str
    target_line: str
    smells: Dict[str, bool] = field(default_factory=dict)
    smell_details: Dict[str, str] = field(default_factory=dict)
    parseable: bool = True

    def any_smell(self) -> bool:
        return any(self.smells.values())

    def smell_count(self) -> int:
        return sum((1 for v in self.smells.values() if v))

def load_jsonl(filepath: Path) -> List[Dict]:
    """Load a JSONL file, returning list of parsed JSON objects."""
    if not filepath.exists():
        return []
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f'Warning: Failed to parse line {line_num} in {filepath}: {e}')
    return data

def clean_markdown(text: str) -> str:
    """Strip markdown code-block fences."""
    if not text:
        return text
    text = re.sub('```python\\s*\\n?', '', text)
    text = re.sub('```\\s*\\n?', '', text)
    text = re.sub('`([^`]+)`', '\\1', text)
    return text.strip()

def _get_test_functions(tree: ast.Module) -> List[ast.FunctionDef]:
    """
    Return all test_* functions reachable from the module level.

    Covers:
      - Top-level functions:     def test_foo(): ...
      - Async top-level:         async def test_foo(): ...
      - TestCase methods:        class TestFoo(unittest.TestCase): def test_foo(self): ...
      - Async TestCase methods:  async def test_foo(self): ...
      - Nested TestCase classes: class Outer: class Inner: def test_foo(self): ...
    """
    _TEST_FUNC_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef)
    funcs: List[ast.FunctionDef] = []

    def _collect(nodes, depth: int=0) -> None:
        for node in nodes:
            if isinstance(node, _TEST_FUNC_TYPES) and node.name.startswith('test'):
                funcs.append(node)
            elif isinstance(node, ast.ClassDef) and depth < 3:
                _collect(ast.iter_child_nodes(node), depth + 1)
    _collect(ast.iter_child_nodes(tree))
    return funcs

def _walk_skip_nested(node: ast.AST):
    """Walk AST nodes but do not descend into nested FunctionDef/AsyncFunctionDef."""
    yield node
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        yield from _walk_skip_nested(child)

def detect_assertion_roulette(func: ast.FunctionDef) -> Tuple[bool, str]:
    """
    Assertion Roulette: >1 assertion and none carry an explanatory message.

    Two assertion styles are counted:
      - pytest/plain style:   assert expr  /  assert expr, "msg"
      - unittest style:       self.assertEqual(a, b)  /  self.assertEqual(a, b, msg="...")

    Message detection:
      - pytest:    assert expr, "msg"   → ast.Assert.msg is not None
      - unittest:  self.assertEqual(a, b, msg="x")  → keyword arg named 'msg'
                   self.assertEqual(a, b, "x")       → positional 3rd argument
    """
    assert_nodes = [n for n in _walk_skip_nested(func) if isinstance(n, ast.Assert)]
    pytest_has_msg = any((n.msg is not None for n in assert_nodes))
    unittest_nodes = []
    for node in _walk_skip_nested(func):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if not (isinstance(f, ast.Attribute) and f.attr.startswith('assert')):
            continue
        if not (isinstance(f.value, ast.Name) and f.value.id == 'self'):
            continue
        unittest_nodes.append(node)

    def _unittest_has_msg(call: ast.Call) -> bool:
        if any((kw.arg == 'msg' for kw in call.keywords)):
            return True
        _RAISES_LIKE = {'assertRaises', 'assertRaisesRegex', 'assertRaisesRegexp', 'assertWarns', 'assertWarnsRegex', 'assertWarnsRegexp'}
        if call.func.attr not in _RAISES_LIKE and len(call.args) >= 3:
            return True
        return False
    unittest_has_msg = any((_unittest_has_msg(n) for n in unittest_nodes))
    total = len(assert_nodes) + len(unittest_nodes)
    if total <= 1:
        return (False, '')
    has_any_msg = pytest_has_msg or unittest_has_msg
    if not has_any_msg:
        return (True, f'{total} assertions ({len(assert_nodes)} assert, {len(unittest_nodes)} unittest), none carry a failure message')
    return (False, '')

def detect_eager_test(func: ast.FunctionDef, func_name: str) -> Tuple[bool, str]:
    """
    Eager Test: the test invokes the function-under-test more than once.

    Handles both direct calls (func_name(...)) and method calls
    (solution.func_name(...), self.func_name(...), obj.func_name(...)).
    """
    if not func_name:
        return (False, '')
    call_count = 0
    for node in _walk_skip_nested(func):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == func_name:
            call_count += 1
        elif isinstance(node.func, ast.Attribute) and node.func.attr == func_name:
            call_count += 1
    if call_count > 1:
        return (True, f"'{func_name}' called {call_count} times in one test")
    return (False, '')

def detect_mystery_guest(func: ast.FunctionDef, tree: ast.Module) -> Tuple[bool, str]:
    """
    Mystery Guest: the test uses external resources (files, network, databases).

    Two complementary checks are applied:

    1. Module-level import check: guest-module imports (network, DB, subprocess)
       are collected at file level, but the smell fires only when a name from those
       imports is actually *used* within this specific test function body. This
       prevents flagging every test in a file just because one test at the top
       imports requests.

    2. Function-call check (MYSTERY_GUEST_FS_CALLS): specific filesystem operations
       called anywhere in the test body, regardless of which module they originate
       from. This catches pathlib.Path.read_text(), os.listdir(), open(), etc.
    """

    def _is_guest_import(dotted_name: str) -> bool:
        base = dotted_name.split('.')[0]
        if base in MYSTERY_GUEST_BASE_MODULES:
            return True
        parts = dotted_name.split('.')
        for i in range(1, len(parts) + 1):
            if '.'.join(parts[:i]) in MYSTERY_GUEST_FULL_MODULES:
                return True
        return False
    guest_names: Dict[str, str] = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _is_guest_import(alias.name):
                    local = alias.asname if alias.asname else alias.name.split('.')[0]
                    guest_names[local] = f"uses '{alias.name}'"
        elif isinstance(node, ast.ImportFrom):
            if node.module and _is_guest_import(node.module):
                for alias in node.names:
                    local = alias.asname if alias.asname else alias.name
                    guest_names[local] = f"uses '{node.module}.{alias.name}'"
    if guest_names:
        for node in _walk_skip_nested(func):
            if isinstance(node, ast.Name) and node.id in guest_names:
                return (True, guest_names[node.id])
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and (node.value.id in guest_names):
                return (True, guest_names[node.value.id])
    for node in _walk_skip_nested(func):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Name) and f.id in MYSTERY_GUEST_FS_CALLS:
            return (True, f'calls {f.id}()')
        if isinstance(f, ast.Attribute) and f.attr in MYSTERY_GUEST_FS_CALLS:
            return (True, f'calls .{f.attr}()')
    return (False, '')

def _has_magic_number(subtree: ast.AST) -> Optional[str]:
    """Return an evidence string if subtree contains a magic numeric literal."""
    for child in ast.walk(subtree):
        if isinstance(child, ast.Constant):
            val = child.value
            if isinstance(val, bool):
                continue
            if isinstance(val, (int, float)) and val not in EXEMPT_NUMBERS:
                return f'magic number {val!r} in assertion'
    return None

def detect_magic_number_test(func: ast.FunctionDef) -> Tuple[bool, str]:
    """
    Magic Number Test: an assertion contains a numeric literal whose meaning
    is not self-evident.

    Exempt values: 0, 0.0, 1, -1, 2, -2 (see EXEMPT_NUMBERS), and booleans.
    Flags any other int or float found inside:
      - pytest-style:          assert expr
      - unittest-style:        self.assertEqual(a, b) / self.assertAlmostEqual(a, b)
      - @pytest.mark.parametrize parameter lists (applies same standard to both styles)
    """
    for dec in func.decorator_list:
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and (dec.func.attr == 'parametrize') and (len(dec.args) >= 2):
            evidence = _has_magic_number(dec.args[1])
            if evidence:
                return (True, f'magic number in @parametrize: {evidence}')
    for node in _walk_skip_nested(func):
        if isinstance(node, ast.Assert):
            evidence = _has_magic_number(node.test)
            if evidence:
                return (True, evidence)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr.startswith('assert') and isinstance(node.func.value, ast.Name) and (node.func.value.id == 'self'):
            for arg in node.args:
                evidence = _has_magic_number(arg)
                if evidence:
                    return (True, evidence)
    return (False, '')

def detect_obscure_test(func: ast.FunctionDef) -> Tuple[bool, str]:
    """
    Obscure Test: the test is difficult to understand at a glance.

    Heuristics:
      - Function body has more than 15 AST statements, OR
      - Function body has more than 5 local assignments
    """

    def _is_docstring_expr(n: ast.AST) -> bool:
        return isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)
    stmt_count = sum((1 for n in _walk_skip_nested(func) if isinstance(n, ast.stmt) and n is not func and (not _is_docstring_expr(n))))
    assign_count = sum((1 for n in _walk_skip_nested(func) if isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign))))
    if stmt_count > 15:
        return (True, f'{stmt_count} statements (threshold: 15)')
    if assign_count > 5:
        return (True, f'{assign_count} assignments (threshold: 5)')
    return (False, '')
_SETUP_METHODS = frozenset({'setUp', 'setUpClass', 'setUpModule', 'setup_method', 'setup_function', 'setup'})

def detect_general_fixture(tree: ast.Module) -> Tuple[bool, str]:
    """
    General Fixture: the test setup initialises more objects than any individual
    test actually needs.

    Heuristic: a setup function/method contains ≥3 assignments.

    Covers setUp, setUpClass, setUpModule, setup_method, setup_function, setup,
    and @pytest.fixture functions.
    """
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            continue
        if isinstance(node, ast.ClassDef):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.FunctionDef) and child.name in _SETUP_METHODS:
                    count = sum((1 for n in ast.walk(child) if isinstance(n, (ast.Assign, ast.AnnAssign))))
                    if count >= 3:
                        return (True, f'{child.name} has {count} assignments')
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name in _SETUP_METHODS:
            count = sum((1 for n in ast.walk(node) if isinstance(n, (ast.Assign, ast.AnnAssign))))
            if count >= 3:
                return (True, f'{node.name} has {count} assignments')
        for dec in node.decorator_list:
            is_fixture = isinstance(dec, ast.Name) and dec.id == 'fixture' or (isinstance(dec, ast.Attribute) and dec.attr == 'fixture') or (isinstance(dec, ast.Call) and (isinstance(dec.func, ast.Name) and dec.func.id == 'fixture' or (isinstance(dec.func, ast.Attribute) and dec.func.attr == 'fixture')))
            if is_fixture:
                count = sum((1 for n in ast.walk(node) if isinstance(n, (ast.Assign, ast.AnnAssign))))
                if count >= 3:
                    return (True, f"fixture '{node.name}' has {count} assignments")
    return (False, '')

def detect_conditional_test_logic(func: ast.FunctionDef) -> Tuple[bool, str]:
    """
    Conditional Test Logic: the test body contains control-flow constructs
    (if, for, while, try/except) which obscure its intent and make it
    non-deterministic in what it actually exercises.
    """
    for node in _walk_skip_nested(func):
        if node is func:
            continue
        if isinstance(node, ast.If):
            return (True, 'contains if statement')
        if isinstance(node, ast.For):
            return (True, 'contains for loop')
        if isinstance(node, ast.While):
            return (True, 'contains while loop')
        if isinstance(node, (ast.Try, ast.TryStar)):
            return (True, 'contains try/except')
        if isinstance(node, ast.IfExp):
            return (True, 'contains conditional expression (ternary)')
    return (False, '')

def detect_fragile_test(func: ast.FunctionDef, tree: ast.Module) -> Tuple[bool, str]:
    """
    Fragile Test: the test depends on external, time-varying, or random state
    that can cause it to break without any code changes.

    Checks:
      - time.sleep() — introduces timing dependency
      - datetime.now() / datetime.today() / datetime.utcnow() — clock dependency
      - random.* calls without a preceding random.seed() in the test file
      - Hardcoded absolute file paths in string literals
    """
    has_random_seed = any((isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and (n.func.attr == 'seed') and (isinstance(n.func.value, ast.Name) and n.func.value.id == 'random' or (isinstance(n.func.value, ast.Attribute) and n.func.value.attr == 'random')) for n in _walk_skip_nested(func)))
    for node in _walk_skip_nested(func):
        if not isinstance(node, ast.Call):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                _UNIX_FS_PREFIXES = ('/home/', '/root/', '/Users/', '/usr/', '/etc/', '/opt/', '/var/lib/', '/var/log/', '/srv/', '/data/', '/mnt/', '/media/', '/tmp/')
                val = node.value
                is_windows_abs = re.match('^[A-Za-z]:\\\\', val)
                is_unix_fs = any((val.startswith(p) for p in _UNIX_FS_PREFIXES))
                if (is_windows_abs or is_unix_fs) and len(val) > 4:
                    return (True, f'hardcoded absolute path: {val[:60]!r}')
            continue
        func_node = node.func
        if not isinstance(func_node, ast.Attribute):
            continue
        attr = func_node.attr
        if attr == 'sleep':
            caller = func_node.value
            if isinstance(caller, ast.Name) and caller.id in {'time', 'asyncio'}:
                return (True, f'calls {caller.id}.sleep()')
        _CLOCK_READS = {'time', 'perf_counter', 'monotonic', 'process_time', 'thread_time', 'gmtime', 'localtime', 'mktime', 'strftime', 'ctime'}
        if attr in _CLOCK_READS:
            caller = func_node.value
            if isinstance(caller, ast.Name) and caller.id == 'time':
                return (True, f'calls time.{attr}() (clock read)')
        if attr in {'uuid4', 'uuid1', 'uuid3', 'uuid5'}:
            caller = func_node.value
            if isinstance(caller, ast.Name) and caller.id == 'uuid':
                return (True, f'calls uuid.{attr}() (non-deterministic)')
        if attr == 'getenv':
            caller = func_node.value
            if isinstance(caller, ast.Name) and caller.id == 'os':
                return (True, 'calls os.getenv() (external environment dependency)')
        if attr in {'now', 'today', 'utcnow'}:
            caller = func_node.value
            if isinstance(caller, ast.Name) and caller.id in {'datetime', 'date'}:
                return (True, f'calls {caller.id}.{attr}()')
            if isinstance(caller, ast.Attribute) and caller.attr in {'datetime', 'date'}:
                return (True, f'calls {caller.attr}.{attr}()')
        _RANDOM_FUNCS = {'random', 'randint', 'choice', 'shuffle', 'sample', 'uniform', 'gauss', 'randrange', 'choices', 'expovariate'}
        if attr in _RANDOM_FUNCS and (not has_random_seed):
            caller = func_node.value
            if isinstance(caller, ast.Name) and caller.id == 'random':
                return (True, f'calls random.{attr}() without seed')
        if attr in _RANDOM_FUNCS and (not has_random_seed):
            caller = func_node.value
            if isinstance(caller, ast.Attribute) and caller.attr == 'random' and isinstance(caller.value, ast.Name) and (caller.value.id in {'np', 'numpy'}):
                return (True, f'calls np.random.{attr}() without seed')
    for node in _walk_skip_nested(func):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name):
            continue
        name = node.func.id
        if name == 'sleep':
            return (True, 'calls sleep() (from time import sleep)')
    for node in _walk_skip_nested(func):
        if isinstance(node, ast.Attribute) and node.attr == 'environ' and isinstance(node.value, ast.Name) and (node.value.id == 'os'):
            return (True, 'accesses os.environ (external environment dependency)')
    return (False, '')

def detect_unknown_test(func: ast.FunctionDef) -> Tuple[bool, str]:
    """
    Unknown Test / Unverified Action: the test function contains no assertions
    at all, providing a false sense of coverage while verifying nothing.

    Assertion forms counted:
      - pytest / plain:       ast.Assert nodes
      - unittest:             self.assert*() method calls
      - pytest.raises()/warns() context managers

    """
    assert_count = sum((1 for n in _walk_skip_nested(func) if isinstance(n, ast.Assert)))
    all_assert_calls = sum((1 for n in _walk_skip_nested(func) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr.startswith('assert')))
    pytest_raises_count = 0
    for node in _walk_skip_nested(func):
        if not isinstance(node, ast.With):
            continue
        for item in node.items:
            ctx = item.context_expr
            if isinstance(ctx, ast.Call) and isinstance(ctx.func, ast.Attribute) and (ctx.func.attr in {'raises', 'warns', 'deprecated_call'}) and isinstance(ctx.func.value, ast.Name) and (ctx.func.value.id == 'pytest'):
                pytest_raises_count += 1
    fail_count = sum((1 for n in _walk_skip_nested(func) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and (n.func.attr == 'fail') and isinstance(n.func.value, ast.Name) and (n.func.value.id in {'self', 'pytest'})))
    if assert_count + all_assert_calls + pytest_raises_count + fail_count == 0:
        return (True, 'test function contains no assertions')
    return (False, '')

def _is_trivial_assert(node: ast.Assert) -> bool:
    """
    Return True if the assert expression matches a trivially weak pattern.

    Patterns (mirroring TRIVIAL_PATTERNS from analyze_assertion_quality.py):
      assert True / assert False          — hardcoded boolean
      assert x is None / is not None      — null check only
      assert isinstance(x, T)             — type check only
      assert x                            — bare variable (no comparison)
      assert x == None                    — equality-to-None
      assert x == [] / {} / ""            — empty container / string
    """
    test = node.test
    if isinstance(test, ast.Constant) and isinstance(test.value, bool):
        return True
    if isinstance(test, ast.Name):
        return True
    if isinstance(test, ast.Call) and isinstance(test.func, ast.Name) and (test.func.id == 'isinstance'):
        return True
    if isinstance(test, ast.Compare) and len(test.ops) == 1:
        op = test.ops[0]
        comp = test.comparators[0]
        if isinstance(op, (ast.Is, ast.IsNot)) and isinstance(comp, ast.Constant) and (comp.value is None):
            return True
        if isinstance(op, (ast.Eq, ast.NotEq)) and isinstance(comp, ast.Constant) and (comp.value is None):
            return True
        if isinstance(op, ast.Eq):
            if isinstance(comp, (ast.List, ast.Set)) and (not comp.elts):
                return True
            if isinstance(comp, ast.Dict) and (not comp.keys):
                return True
            if isinstance(comp, ast.Constant) and comp.value == '':
                return True
    return False

def _is_trivial_unittest_call(call: ast.Call) -> bool:
    """
    Return True if a self.assert*() call is trivially weak.

    Always trivial:
      assertIsNone / assertIsNotNone     — null checks only
      assertIsInstance                   — type check only

    Conditionally trivial:
      assertTrue(x) / assertFalse(x)    — trivial only if the argument is itself
        a bare variable, a bool constant, or an isinstance() call.
        assertTrue(result > 0) or assertFalse(result != expected) are NOT trivial
        because the argument expresses a meaningful quantitative condition.
    """
    attr = call.func.attr
    if attr in {'assertIsNone', 'assertIsNotNone', 'assertIsInstance'}:
        return True
    if attr in {'assertTrue', 'assertFalse'} and call.args:
        arg = call.args[0]
        if isinstance(arg, ast.Name):
            return True
        if isinstance(arg, ast.Constant) and isinstance(arg.value, bool):
            return True
        if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and (arg.func.id == 'isinstance'):
            return True
        return False
    return False

def detect_trivial_assertion(func: ast.FunctionDef) -> Tuple[bool, str]:
    """
    Trivial / Suboptimal Assertion: ALL assertions in the test verify only
    trivially weak conditions (null checks, type checks, bare booleans, empty
    containers) rather than meaningful return values or side effects.

    The smell fires only when at least one assertion exists but every single one
    is trivial. A test with NO assertions is Unknown Test, not this smell.

    Alves et al. (2025); Sandoval Alcocer et al. (2026)
    """
    assert_nodes = [n for n in _walk_skip_nested(func) if isinstance(n, ast.Assert)]
    unittest_nodes = [n for n in _walk_skip_nested(func) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr.startswith('assert') and isinstance(n.func.value, ast.Name) and (n.func.value.id == 'self')]
    total = len(assert_nodes) + len(unittest_nodes)
    if total == 0:
        return (False, '')
    trivial_count = sum((1 for n in assert_nodes if _is_trivial_assert(n))) + sum((1 for n in unittest_nodes if _is_trivial_unittest_call(n)))
    if trivial_count == total:
        return (True, f'all {total} assertion(s) are trivially weak (null/type/bool checks)')
    return (False, '')

def detect_duplicated_setup(test_funcs: List[ast.FunctionDef]) -> Tuple[bool, str]:
    """
    Duplicated Setup: multiple test functions in the same file share identical
    top-level initialisation assignments, inflating test suite size and
    complicating maintenance (e.g. every function starts with
    `solution = Solution()`).

    Detection: compare direct-child ast.Assign nodes across all test functions.
    Two assignments are considered identical if they have the same target name
    and structurally identical right-hand sides (via ast.dump).

    Only direct-child assignments are checked (not those inside loops/conditions)
    because setup code is typically at the top of the function body.

    Sandoval Alcocer et al. (2026)
    """
    if len(test_funcs) < 2:
        return (False, '')
    assignment_funcs: Dict[str, List[str]] = defaultdict(list)
    for func in test_funcs:
        seen_in_this_func = set()
        for node in ast.iter_child_nodes(func):
            target = None
            value = None
            if isinstance(node, ast.Assign):
                if len(node.targets) != 1:
                    continue
                target = node.targets[0]
                value = node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                target = node.target
                value = node.value
            if target is None or value is None:
                continue
            if not isinstance(target, (ast.Name, ast.Attribute)):
                continue
            target_name = target.id if isinstance(target, ast.Name) else target.attr
            key = f'{target_name}={ast.dump(value)}'
            if key not in seen_in_this_func:
                seen_in_this_func.add(key)
                assignment_funcs[key].append(func.name)
    duplicates = {k: funcs for k, funcs in assignment_funcs.items() if len(funcs) >= 2}
    if duplicates:
        worst_key = max(duplicates, key=lambda k: len(duplicates[k]))
        target_name = worst_key.split('=')[0]
        count = len(duplicates[worst_key])
        return (True, f"'{target_name}' setup repeated identically in {count} test functions")
    return (False, '')

def analyze_test_code(test_code: str, func_name: str) -> Tuple[Dict[str, bool], Dict[str, str], bool]:
    """
    Analyse one test-code string for all 8 smells.

    Returns:
        smells      - dict mapping smell name → bool (True = smell detected)
        details     - dict mapping smell name → evidence string
        parseable   - False if the code could not be parsed
    """
    smells = {s: False for s in SMELL_NAMES}
    details = {s: '' for s in SMELL_NAMES}
    cleaned = clean_markdown(test_code)
    if not cleaned:
        return (smells, details, False)
    try:
        tree = ast.parse(cleaned)
    except SyntaxError:
        return (smells, details, False)
    test_funcs = _get_test_functions(tree)
    for smell_name, detector in [('general_fixture', lambda: detect_general_fixture(tree)), ('duplicated_setup', lambda: detect_duplicated_setup(test_funcs))]:
        found, detail = detector()
        smells[smell_name] = found
        details[smell_name] = detail
    detectors = [('assertion_roulette', lambda f: detect_assertion_roulette(f)), ('eager_test', lambda f: detect_eager_test(f, func_name)), ('mystery_guest', lambda f: detect_mystery_guest(f, tree)), ('magic_number_test', lambda f: detect_magic_number_test(f)), ('obscure_test', lambda f: detect_obscure_test(f)), ('conditional_test_logic', lambda f: detect_conditional_test_logic(f)), ('fragile_test', lambda f: detect_fragile_test(f, tree)), ('unknown_test', lambda f: detect_unknown_test(f)), ('trivial_assertion', lambda f: detect_trivial_assertion(f))]
    for func in test_funcs:
        for smell_name, detector in detectors:
            if not smells[smell_name]:
                found, detail = detector(func)
                smells[smell_name] = found
                details[smell_name] = detail
    return (smells, details, True)
