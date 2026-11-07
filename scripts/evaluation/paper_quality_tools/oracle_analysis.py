"""Conservative classification and runtime tracking of generated-test oracles.

This module intentionally does not replace the legacy ``has_assertions`` field.
It provides a separate, auditable measurement path whose unit is an oracle site.
Unknown forms do not satisfy either quality gate.
"""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Iterable


class OracleClass(str, Enum):
    TRIVIAL = "TRIVIAL"
    WEAK = "WEAK"
    STRONG = "STRONG"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class OracleSite:
    oracle_id: str
    oracle_kind: str
    oracle_class: OracleClass
    lineno: int
    col_offset: int
    sut_dependent: bool | None
    classification_reason: str

    def to_dict(self) -> dict:
        row = asdict(self)
        row["oracle_class"] = self.oracle_class.value
        return row


_MOCK_CONTRACTS = {
    "assert_called", "assert_called_once", "assert_called_with",
    "assert_called_once_with", "assert_any_call", "assert_has_calls",
    "assert_not_called", "assert_awaited", "assert_awaited_once",
    "assert_awaited_with", "assert_awaited_once_with", "assert_any_await",
    "assert_has_awaits", "assert_not_awaited",
}
_WEAK_ASSERT_METHODS = {"assertIsNone", "assertIsNotNone", "assertIsInstance", "assertNotIsInstance"}
_TRUTH_ASSERT_METHODS = {"assertTrue", "assertFalse"}
_STRONG_ASSERT_METHODS = {
    "assertEqual", "assertNotEqual", "assertAlmostEqual", "assertNotAlmostEqual",
    "assertGreater", "assertGreaterEqual", "assertLess", "assertLessEqual",
    "assertIn", "assertNotIn", "assertIs", "assertIsNot", "assertRegex",
    "assertNotRegex", "assertCountEqual", "assertSequenceEqual", "assertListEqual",
    "assertTupleEqual", "assertSetEqual", "assertDictEqual", "assertMultiLineEqual",
    "assertRaises", "assertRaisesRegex", "assertWarns", "assertWarnsRegex",
}
_NON_SUT_CALLS = {
    "bool", "bytes", "dict", "float", "frozenset", "int", "list", "set", "str", "tuple",
    "MagicMock", "Mock", "PropertyMock", "mock_open", "patch", "range",
}
_MOCK_CONSTRUCTORS = {"Mock", "MagicMock", "AsyncMock", "PropertyMock", "mock_open"}
_STRONG_PROPERTY_METHODS = {
    "startswith", "endswith", "equals", "issubset", "issuperset", "isdisjoint",
    "exists", "is_file", "is_dir",
}
_NUMPY_PROPERTY_CALLS = {
    "np.allclose", "numpy.allclose", "np.array_equal", "numpy.array_equal",
    "np.isclose", "numpy.isclose", "np.all", "numpy.all",
    "torch.allclose", "torch.equal",
}
_ENVIRON_SENTINEL = "$os_environ$"
_REDIRECT_CONTEXTS = {"redirect_stdout", "redirect_stderr",
                      "contextlib.redirect_stdout", "contextlib.redirect_stderr"}
_BOGUS_MOCK_CALL_ATTRS = {"called_once_with"}


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _qualified_name(node: ast.AST) -> str | None:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def _constant_value(node: ast.AST) -> tuple[bool, object]:
    """Safely fold a small, side-effect-free expression subset; never uses eval."""
    if isinstance(node, ast.Constant):
        return True, node.value
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values = [_constant_value(e) for e in node.elts]
        if not all(ok for ok, _ in values):
            return False, None
        raw = [v for _, v in values]
        return True, tuple(raw) if isinstance(node, ast.Tuple) else set(raw) if isinstance(node, ast.Set) else raw
    if isinstance(node, ast.Dict):
        keys = [_constant_value(k) for k in node.keys]
        vals = [_constant_value(v) for v in node.values]
        if not all(ok for ok, _ in keys + vals):
            return False, None
        try:
            return True, {k: v for (_, k), (_, v) in zip(keys, vals)}
        except (TypeError, ValueError):
            return False, None
    if isinstance(node, ast.UnaryOp):
        ok, value = _constant_value(node.operand)
        if not ok:
            return False, None
        try:
            if isinstance(node.op, ast.Not): return True, not value
            if isinstance(node.op, ast.USub): return True, -value
            if isinstance(node.op, ast.UAdd): return True, +value
        except (TypeError, ValueError):
            return False, None
    if isinstance(node, ast.BinOp):
        left_ok, left = _constant_value(node.left)
        right_ok, right = _constant_value(node.right)
        if not (left_ok and right_ok):
            return False, None
        try:
            if isinstance(node.op, ast.Add): return True, left + right
            if isinstance(node.op, ast.Sub): return True, left - right
            if isinstance(node.op, ast.Mult): return True, left * right
            if isinstance(node.op, ast.Div): return True, left / right
            if isinstance(node.op, ast.FloorDiv): return True, left // right
            if isinstance(node.op, ast.Mod): return True, left % right
            if isinstance(node.op, ast.Pow): return True, left ** right
        except (ArithmeticError, TypeError, ValueError):
            return False, None
    if isinstance(node, ast.Compare) and len(node.ops) == len(node.comparators) == 1:
        lok, left = _constant_value(node.left)
        rok, right = _constant_value(node.comparators[0])
        if not (lok and rok):
            return False, None
        op = node.ops[0]
        try:
            if isinstance(op, ast.Eq): return True, left == right
            if isinstance(op, ast.NotEq): return True, left != right
            if isinstance(op, ast.Is): return True, left is right
            if isinstance(op, ast.IsNot): return True, left is not right
            if isinstance(op, ast.Lt): return True, left < right
            if isinstance(op, ast.LtE): return True, left <= right
            if isinstance(op, ast.Gt): return True, left > right
            if isinstance(op, ast.GtE): return True, left >= right
            if isinstance(op, ast.In): return True, left in right
            if isinstance(op, ast.NotIn): return True, left not in right
        except (TypeError, ValueError):
            return False, None
    return False, None


def _contains_derived(node: ast.AST, derived: set[str]) -> bool:
    return any(isinstance(n, ast.Name) and n.id in derived for n in ast.walk(node))


def _normalize_focal_name(name: str) -> str:
    """Underscore-prefix-insensitive form, since generated tests sometimes call a
    focal function's public alias (or vice versa) rather than its recorded name."""
    return name.lstrip("_")


def _call_is_focal(call: ast.Call, sut_names: set[str], focal_aliases: set[str]) -> bool:
    qname = _qualified_name(call.func)
    name = _call_name(call.func)
    if name in focal_aliases:
        return True
    if name and any(_normalize_focal_name(name) == _normalize_focal_name(s) for s in sut_names):
        return True
    return bool(qname and any(part in sut_names for part in qname.split(".")))


def _is_environ_access(node: ast.AST) -> bool:
    if isinstance(node, ast.Subscript):
        return _qualified_name(node.value) == "os.environ"
    if isinstance(node, ast.Call):
        qname = _qualified_name(node.func) or ""
        return qname in {"os.getenv", "os.environ.get"}
    if isinstance(node, ast.Attribute):
        return _qualified_name(node) == "os.environ"
    return False


def _expr_is_derived(node: ast.AST, derived: set[str], sut_names: set[str],
                     focal_aliases: set[str] | None = None) -> bool:
    aliases = focal_aliases or set()
    if _contains_derived(node, derived):
        return True
    if _ENVIRON_SENTINEL in derived and any(_is_environ_access(sub) for sub in ast.walk(node)):
        return True
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call) and _call_is_focal(sub, sut_names, aliases):
            return True
        if isinstance(sub, ast.Name) and sub.id in aliases:
            return True
        if isinstance(sub, ast.Attribute):
            qname = _qualified_name(sub)
            if qname and any(part in sut_names for part in qname.split(".")):
                return True
    return False


def _rhs_is_derived(node: ast.AST, derived: set[str], sut_names: set[str],
                    focal_aliases: set[str] | None = None) -> bool:
    """Backward-compatible name for assignment/expression provenance checks."""
    if _expr_is_derived(node, derived, sut_names, focal_aliases):
        return True
    if not sut_names:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                qname = _qualified_name(sub.func)
                name = _call_name(sub.func)
                if qname not in {"pytest.approx"} and name not in _NON_SUT_CALLS:
                    return True
    return False


def _expr_is_mock_derived(node: ast.AST, mock_derived: set[str]) -> bool:
    return any(isinstance(n, ast.Name) and n.id in mock_derived for n in ast.walk(node))


_MOCK_CALL_CAPTURE_ATTRS = {"call_args", "call_args_list", "await_args", "await_args_list"}


def _rhs_is_mock_call_capture(node: ast.AST, mock_derived: set[str]) -> bool:
    """A mock's recorded call arguments are SUT-derived state (what the focal call
    was invoked with), even though the mock object itself is not."""
    return any(isinstance(n, ast.Attribute) and n.attr in _MOCK_CALL_CAPTURE_ATTRS
               and _expr_is_mock_derived(n.value, mock_derived) for n in ast.walk(node))


def _rhs_is_mock(node: ast.AST, mock_derived: set[str]) -> bool:
    if _expr_is_mock_derived(node, mock_derived):
        return True
    return any(isinstance(n, ast.Call) and _call_name(n.func) in _MOCK_CONSTRUCTORS
               for n in ast.walk(node))


def _assigned_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
            names.add(sub.id)
    return names


def _combine_predicate_classes(parts: list[tuple[OracleClass, bool | None, str]]) -> tuple[OracleClass, bool | None, str]:
    classes = [part[0] for part in parts]
    depends = any(part[1] is True for part in parts)
    if OracleClass.UNKNOWN in classes:
        return OracleClass.UNKNOWN, depends or None, "compound_contains_unknown_branch"
    if OracleClass.STRONG in classes:
        return OracleClass.STRONG, depends, "compound_with_strong_recognized_branch"
    if OracleClass.WEAK in classes:
        return OracleClass.WEAK, depends, "compound_all_sut_branches_weak"
    if classes and all(cls is OracleClass.TRIVIAL for cls in classes):
        return OracleClass.TRIVIAL, False, "compound_statically_satisfied"
    return OracleClass.UNKNOWN, depends or None, "compound_predicate_not_safely_classified"


def _classify_assert(expr: ast.AST, derived: set[str], sut_names: set[str] | None = None,
                     focal_aliases: set[str] | None = None,
                     mock_derived: set[str] | None = None) -> tuple[OracleClass, bool | None, str]:
    sut_names = sut_names or set()
    focal_aliases = focal_aliases or set()
    mock_derived = mock_derived or set()
    folded, value = _constant_value(expr)
    if folded:
        if bool(value):
            return OracleClass.TRIVIAL, False, "statically_satisfied_constant"
        return OracleClass.UNKNOWN, False, "statically_failing_constant"

    depends = _expr_is_derived(expr, derived, sut_names, focal_aliases)
    if isinstance(expr, ast.BoolOp):
        return _combine_predicate_classes([
            _classify_assert(value, derived, sut_names, focal_aliases, mock_derived)
            for value in expr.values
        ])
    if isinstance(expr, ast.Name):
        if depends:
            return OracleClass.WEAK, True, "sut_derived_truthiness"
        return OracleClass.UNKNOWN, None, "unresolved_name_truthiness"
    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
        inner = _classify_assert(expr.operand, derived, sut_names, focal_aliases, mock_derived)
        if inner[0] in {OracleClass.WEAK, OracleClass.STRONG}:
            return inner[0], inner[1], "negated_" + inner[2]
        if depends:
            return OracleClass.WEAK, True, "sut_derived_negated_truthiness"
        return OracleClass.UNKNOWN, None, "unresolved_negated_truthiness"
    if isinstance(expr, ast.Call) and _call_name(expr.func) in {"isinstance", "hasattr", "callable"}:
        if (_call_name(expr.func) == "hasattr" and len(expr.args) >= 2
                and isinstance(expr.args[1], ast.Constant)
                and expr.args[1].value in sut_names):
            return OracleClass.WEAK, True, "focal_member_existence"
        if depends:
            reason = {"isinstance": "sut_derived_runtime_type", "hasattr": "sut_derived_attribute_existence",
                      "callable": "sut_derived_callability"}[_call_name(expr.func)]
            return OracleClass.WEAK, True, reason
        return OracleClass.UNKNOWN, None, "coarse_check_without_sut_provenance"
    if isinstance(expr, ast.Compare):
        if _expr_is_mock_derived(expr, mock_derived) and any(
                isinstance(n, ast.Attribute) and n.attr in {
                    "call_count", "call_args", "call_args_list", "mock_calls", "await_count", "await_args_list"
                } for n in ast.walk(expr)):
            return OracleClass.STRONG, True, "mock_state_comparison_contract"
        if len(expr.ops) == 1 and isinstance(expr.ops[0], (ast.Is, ast.IsNot)):
            right = expr.comparators[0]
            if isinstance(right, ast.Constant) and right.value is None and depends:
                return OracleClass.WEAK, True, "sut_derived_nullity"
            # Identity with itself is not a useful semantic contract.
            if ast.dump(expr.left, include_attributes=False) == ast.dump(right, include_attributes=False):
                return OracleClass.UNKNOWN, depends or None, "self_identity_comparison"
        if len(expr.ops) == 1 and isinstance(expr.ops[0], (ast.Eq, ast.NotEq)):
            right = expr.comparators[0]
            if ((isinstance(right, ast.Constant) and right.value is None)
                    or (isinstance(expr.left, ast.Constant) and expr.left.value is None)) and depends:
                return OracleClass.WEAK, True, "sut_derived_nullity"
        if depends:
            return OracleClass.STRONG, True, "sut_derived_specific_comparison"
        return OracleClass.UNKNOWN, None, "comparison_without_sut_provenance"
    if isinstance(expr, ast.Call):
        name = _call_name(expr.func)
        qname = _qualified_name(expr.func) or ""
        if name in _BOGUS_MOCK_CALL_ATTRS:
            receiver = expr.func.value if isinstance(expr.func, ast.Attribute) else None
            if receiver is not None and _expr_is_mock_derived(receiver, mock_derived):
                # Not a real unittest.mock API (real: assert_called_once_with); a bare
                # attribute access on a Mock auto-vivifies a truthy child MagicMock and
                # verifies nothing, regardless of the mock's actual call history.
                return OracleClass.TRIVIAL, False, "bogus_mock_attribute_vacuous"
        if name in {"startswith", "endswith", "equals", "issubset", "issuperset", "isdisjoint"}:
            receiver = expr.func.value if isinstance(expr.func, ast.Attribute) else None
            if receiver is not None and _expr_is_derived(receiver, derived, sut_names, focal_aliases):
                return OracleClass.STRONG, True, f"sut_derived_property_{name}"
        if name in {"exists", "is_file", "is_dir"}:
            receiver = expr.func.value if isinstance(expr.func, ast.Attribute) else None
            if receiver is not None and _expr_is_derived(receiver, derived, sut_names, focal_aliases):
                return OracleClass.STRONG, True, f"sut_derived_path_property_{name}"
        if name in {"all", "any"} and expr.args:
            arg = expr.args[0]
            generator_derived = set(derived)
            recognized = bool(isinstance(arg, (ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp)) and arg.generators)
            if recognized:
                for gen in arg.generators:
                    if not _expr_is_derived(gen.iter, generator_derived, sut_names, focal_aliases):
                        recognized = False
                        break
                    generator_derived.update(_assigned_names(gen.target))
            if recognized:
                return OracleClass.STRONG, True, f"sut_derived_quantified_property_{name}"
        if qname in _NUMPY_PROPERTY_CALLS and any(
                _expr_is_derived(arg, derived, sut_names, focal_aliases) for arg in expr.args):
            return OracleClass.STRONG, True, f"sut_derived_numpy_property_{qname.split('.')[-1]}"
        if name == "len" and depends:
            return OracleClass.STRONG, True, "sut_derived_nonempty_length"
        if _call_is_focal(expr, sut_names, focal_aliases):
            # A bare `assert focal(...)` with no recognized call-form is still a
            # coarse truthiness check directly on the SUT return value.
            return OracleClass.WEAK, True, "sut_derived_truthiness_direct_focal_call"
        return OracleClass.UNKNOWN, depends or None, "opaque_predicate_call"
    if isinstance(expr, ast.Attribute) and expr.attr in {"called", "called_once"}:
        if _expr_is_mock_derived(expr.value, mock_derived):
            if expr.attr == "called_once":
                # Not a real unittest.mock API (real: assert_called_once()); a bare
                # attribute access auto-vivifies a truthy child MagicMock.
                return OracleClass.TRIVIAL, False, "bogus_mock_attribute_vacuous"
            return OracleClass.STRONG, True, f"mock_state_contract_{expr.attr}"
        return OracleClass.UNKNOWN, None, "mock_state_without_mock_provenance"
    if depends:
        if isinstance(expr, (ast.Attribute, ast.Subscript)):
            return OracleClass.WEAK, True, "sut_derived_truthiness"
        if isinstance(expr, ast.BinOp):
            return OracleClass.UNKNOWN, True, "compound_predicate_not_safely_classified"
    return OracleClass.UNKNOWN, None, "unrecognized_assertion_form"


def _oracle_descriptor(stmt: ast.stmt, derived: set[str], sut_names: set[str] | None = None,
                       focal_aliases: set[str] | None = None,
                       mock_derived: set[str] | None = None) -> tuple[str, OracleClass, bool | None, str] | None:
    sut_names = sut_names or set()
    focal_aliases = focal_aliases or set()
    mock_derived = mock_derived or set()
    if isinstance(stmt, ast.Assert):
        cls, dep, reason = _classify_assert(stmt.test, derived, sut_names, focal_aliases, mock_derived)
        return "assert", cls, dep, reason
    if isinstance(stmt, ast.With):
        for item in stmt.items:
            call = item.context_expr
            if isinstance(call, ast.Call):
                qname = _qualified_name(call.func) or ""
                name = _call_name(call.func)
                if qname.endswith("pytest.raises") or name in {"assertRaises", "assertRaisesRegex"}:
                    depends = any(_expr_is_derived(node, derived, sut_names, focal_aliases) for node in stmt.body)
                    return "exception_contract", OracleClass.STRONG if depends else OracleClass.UNKNOWN, depends or None, "expected_exception_contract" if depends else "exception_contract_without_sut_provenance"
                if qname.endswith("pytest.warns") or name in {"assertWarns", "assertWarnsRegex"}:
                    depends = any(_expr_is_derived(node, derived, sut_names, focal_aliases) for node in stmt.body)
                    return "warning_contract", OracleClass.STRONG if depends else OracleClass.UNKNOWN, depends or None, "expected_warning_contract" if depends else "warning_contract_without_sut_provenance"
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        call = stmt.value
        name = _call_name(call.func)
        qname = _qualified_name(call.func) or ""
        if name in _MOCK_CONTRACTS:
            receiver = call.func.value if isinstance(call.func, ast.Attribute) else None
            valid = receiver is not None and _expr_is_mock_derived(receiver, mock_derived)
            return "mock_contract", OracleClass.STRONG if valid else OracleClass.UNKNOWN, valid or None, f"interaction_contract_{name}" if valid else "mock_contract_without_mock_provenance"
        if name in _TRUTH_ASSERT_METHODS and call.args:
            predicate = call.args[0] if name == "assertTrue" else ast.UnaryOp(ast.Not(), call.args[0])
            cls, dep, reason = _classify_assert(predicate, derived, sut_names, focal_aliases, mock_derived)
            return "unittest_assertion", cls, dep, f"unittest_{name}_{reason}"
        if name in _WEAK_ASSERT_METHODS:
            depends = any(_expr_is_derived(arg, derived, sut_names, focal_aliases) for arg in call.args)
            return "unittest_assertion", OracleClass.WEAK if depends else OracleClass.UNKNOWN, depends or None, "coarse_unittest_contract" if depends else "unittest_contract_without_sut_provenance"
        if name in _STRONG_ASSERT_METHODS:
            if name in {"assertRaises", "assertRaisesRegex", "assertWarns", "assertWarnsRegex"}:
                depends = any(_expr_is_derived(arg, derived, sut_names, focal_aliases) for arg in call.args[1:])
            else:
                depends = any(_expr_is_derived(arg, derived, sut_names, focal_aliases) for arg in call.args)
            return "unittest_assertion", OracleClass.STRONG if depends else OracleClass.UNKNOWN, depends or None, f"specific_unittest_contract_{name}" if depends else "unittest_contract_without_sut_provenance"
        if qname.startswith(("np.testing.assert", "numpy.testing.assert")):
            depends = any(_expr_is_derived(arg, derived, sut_names, focal_aliases) for arg in call.args)
            return "unittest_assertion", OracleClass.STRONG if depends else OracleClass.UNKNOWN, depends or None, "numpy_testing_contract" if depends else "numpy_testing_without_sut_provenance"
    return None


class _Analyzer:
    def __init__(self, sut_names: Iterable[str] = ()):
        self.sut_names = set(sut_names)
        self.sites: list[OracleSite] = []

    def analyze_block(self, statements: list[ast.stmt], inherited: set[str] | None = None,
                      inherited_mocks: set[str] | None = None,
                      inherited_aliases: set[str] | None = None) -> tuple[set[str], set[str], set[str]]:
        derived = set(inherited or ())
        mocks = set(inherited_mocks or ())
        aliases = set(inherited_aliases or ())
        for stmt in statements:
            if isinstance(stmt, ast.ImportFrom):
                for alias in stmt.names:
                    if alias.name in self.sut_names:
                        aliases.add(alias.asname or alias.name)
            descriptor = _oracle_descriptor(stmt, derived, self.sut_names, aliases, mocks)
            if descriptor:
                kind, cls, dep, reason = descriptor
                self.sites.append(OracleSite("", kind, cls, stmt.lineno, stmt.col_offset, dep, reason))

            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if _call_is_focal(call, self.sut_names, aliases):
                    # A focal method may mutate its receiver and mutable arguments;
                    # subsequent checks of those values are state-transition oracles.
                    if isinstance(call.func, ast.Attribute):
                        derived.update(n.id for n in ast.walk(call.func.value) if isinstance(n, ast.Name))
                    for arg in (*call.args, *(kw.value for kw in call.keywords)):
                        derived.update(n.id for n in ast.walk(arg) if isinstance(n, ast.Name))
                if (isinstance(call.func, ast.Attribute)
                        and call.func.attr in {"append", "extend", "add", "update"}
                        and any(_expr_is_derived(arg, derived, self.sut_names, aliases) for arg in call.args)):
                    derived.update(n.id for n in ast.walk(call.func.value) if isinstance(n, ast.Name))

            if any(isinstance(n, ast.Call) and _call_is_focal(n, self.sut_names, aliases)
                   for n in ast.walk(stmt)):
                derived.add(_ENVIRON_SENTINEL)

            if isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
                value = stmt.value
                targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
                names = set().union(*(_assigned_names(t) for t in targets))
                if value is not None and (_rhs_is_derived(value, derived, self.sut_names, aliases)
                                          or _rhs_is_mock_call_capture(value, mocks)):
                    derived.update(names)
                else:
                    derived.difference_update(names)
                if value is not None and _rhs_is_mock(value, mocks):
                    mocks.update(names)
                else:
                    mocks.difference_update(names)

            child_blocks: list[list[ast.stmt]] = []
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                mock_args = {arg.arg for arg in (*stmt.args.posonlyargs, *stmt.args.args, *stmt.args.kwonlyargs)
                             if arg.arg.startswith("mock") or arg.arg.endswith("_mock")}
                self.analyze_block(stmt.body, set(), mock_args, aliases)
                continue
            if isinstance(stmt, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith)):
                child_blocks.append(stmt.body)
                child_blocks.extend([stmt.orelse] if hasattr(stmt, "orelse") else [])
            elif isinstance(stmt, ast.Try):
                self.analyze_block(stmt.body, derived, mocks, aliases)
                try_has_focal = any(isinstance(n, ast.Call) and _call_is_focal(n, self.sut_names, aliases)
                                    for body_stmt in stmt.body for n in ast.walk(body_stmt))
                for handler in stmt.handlers:
                    handler_derived = set(derived)
                    if try_has_focal and handler.name:
                        handler_derived.add(handler.name)
                    self.analyze_block(handler.body, handler_derived, mocks, aliases)
                if stmt.orelse:
                    self.analyze_block(stmt.orelse, derived, mocks, aliases)
                if stmt.finalbody:
                    self.analyze_block(stmt.finalbody, derived, mocks, aliases)
                continue
            elif isinstance(stmt, ast.Match):
                child_blocks.extend(case.body for case in stmt.cases)
            for block in child_blocks:
                if block:
                    child_derived = set(derived)
                    child_mocks = set(mocks)
                    if isinstance(stmt, (ast.For, ast.AsyncFor)) and _expr_is_derived(stmt.iter, derived, self.sut_names, aliases):
                        child_derived.update(_assigned_names(stmt.target))
                    if isinstance(stmt, (ast.With, ast.AsyncWith)):
                        block_has_focal = any(isinstance(n, ast.Call) and _call_is_focal(n, self.sut_names, aliases)
                                              for body_stmt in block for n in ast.walk(body_stmt))
                        for item in stmt.items:
                            qname = (_qualified_name(item.context_expr.func) or "") if isinstance(item.context_expr, ast.Call) else ""
                            if (qname == "patch" or qname.endswith(".patch") or qname.endswith("patch.object")) and item.optional_vars:
                                child_mocks.update(_assigned_names(item.optional_vars))
                            if qname in _REDIRECT_CONTEXTS and block_has_focal:
                                for arg in item.context_expr.args:
                                    if isinstance(arg, ast.Name):
                                        child_derived.add(arg.id)
                    returned = self.analyze_block(block, child_derived, child_mocks, aliases)
                    if isinstance(stmt, (ast.With, ast.AsyncWith)):
                        derived, mocks, aliases = returned
                    elif isinstance(stmt, (ast.For, ast.AsyncFor)) and block is stmt.body:
                        loop_targets = _assigned_names(stmt.target)
                        derived.update(returned[0] - loop_targets)
                        mocks.update(returned[1] - loop_targets)
        return derived, mocks, aliases


def classify_oracles(source: str, sut_names: Iterable[str] = ()) -> list[OracleSite]:
    tree = ast.parse(source)
    analyzer = _Analyzer(sut_names)
    analyzer.analyze_block(tree.body)
    ordered = sorted(analyzer.sites, key=lambda s: (s.lineno, s.col_offset, s.oracle_kind))
    return [OracleSite(f"oracle_{i:04d}", s.oracle_kind, s.oracle_class, s.lineno,
                       s.col_offset, s.sut_dependent, s.classification_reason)
            for i, s in enumerate(ordered, 1)]


class _Instrumenter(ast.NodeTransformer):
    def __init__(self, sites: list[OracleSite]):
        self.by_location = {(s.lineno, s.col_offset, s.oracle_kind): s for s in sites}

    @staticmethod
    def _record(site: OracleSite) -> ast.Expr:
        call = ast.Expr(ast.Call(ast.Name("__record_oracle_execution__", ast.Load()),
                                 [ast.Constant(site.oracle_id)], []))
        return ast.copy_location(call, ast.Constant(value=None, lineno=site.lineno, col_offset=site.col_offset))

    def _instrument_block(self, body: list[ast.stmt]) -> list[ast.stmt]:
        output: list[ast.stmt] = []
        for stmt in body:
            stmt = self.visit(stmt)
            descriptor_kind = None
            if isinstance(stmt, ast.Assert): descriptor_kind = "assert"
            elif isinstance(stmt, ast.With):
                descriptor_kind = "exception_contract" if any(isinstance(i.context_expr, ast.Call) and ((_qualified_name(i.context_expr.func) or "").endswith("pytest.raises") or _call_name(i.context_expr.func) in {"assertRaises", "assertRaisesRegex"}) for i in stmt.items) else "warning_contract" if any(isinstance(i.context_expr, ast.Call) and ((_qualified_name(i.context_expr.func) or "").endswith("pytest.warns") or _call_name(i.context_expr.func) in {"assertWarns", "assertWarnsRegex"}) for i in stmt.items) else None
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                name = _call_name(stmt.value.func)
                if name in _MOCK_CONTRACTS: descriptor_kind = "mock_contract"
                elif name in _WEAK_ASSERT_METHODS | _STRONG_ASSERT_METHODS | _TRUTH_ASSERT_METHODS: descriptor_kind = "unittest_assertion"
                elif (_qualified_name(stmt.value.func) or "").startswith(("np.testing.assert", "numpy.testing.assert")): descriptor_kind = "unittest_assertion"
            site = self.by_location.get((getattr(stmt, "lineno", -1), getattr(stmt, "col_offset", -1), descriptor_kind))
            if site:
                output.append(self._record(site))
            output.append(stmt)
        return output

    def generic_visit(self, node):
        for field, value in ast.iter_fields(node):
            if isinstance(value, list) and value and all(isinstance(x, ast.stmt) for x in value):
                setattr(node, field, self._instrument_block(value))
            elif isinstance(value, ast.AST):
                setattr(node, field, self.visit(value))
        return node


_RECORDER_SOURCE = '''
import builtins as __oracle_builtins__
__ORACLE_REAL_OPEN__ = __oracle_builtins__.open
__ORACLE_REAL_STR__ = __oracle_builtins__.str

def __record_oracle_execution__(oracle_id):
    import json as __oracle_json
    import os as __oracle_os
    __oracle_path = __oracle_os.environ.get("ORACLE_EXECUTION_FILE")
    if __oracle_builtins__.isinstance(__oracle_path, __ORACLE_REAL_STR__) and __oracle_path:
        with __ORACLE_REAL_OPEN__(__oracle_path, "a", encoding="utf-8") as __oracle_stream:
            __oracle_stream.write(__oracle_json.dumps({"oracle_id": oracle_id}) + "\\n")
'''


def instrument_oracles(source: str, sut_names: Iterable[str] = ()) -> tuple[str, list[OracleSite]]:
    sites = classify_oracles(source, sut_names)
    tree = ast.parse(source)
    tree = _Instrumenter(sites).visit(tree)
    recorder = ast.parse(_RECORDER_SOURCE).body
    insert_at = 0
    while insert_at < len(tree.body) and isinstance(tree.body[insert_at], (ast.Import, ast.ImportFrom)):
        if isinstance(tree.body[insert_at], ast.ImportFrom) and tree.body[insert_at].module == "__future__":
            insert_at += 1
        else:
            break
    tree.body[insert_at:insert_at] = recorder
    ast.fix_missing_locations(tree)
    return ast.unparse(tree), sites


def suite_category(sites: Iterable[OracleSite], executed_ids: set[str]) -> str:
    classes = {s.oracle_class for s in sites if s.oracle_id in executed_ids}
    if OracleClass.STRONG in classes: return "strong-present"
    if OracleClass.WEAK in classes: return "weak-only"
    if OracleClass.TRIVIAL in classes: return "trivial-only"
    if OracleClass.UNKNOWN in classes: return "unknown-only"
    return "no-executed-oracle"


def gate_outcomes(suite_passed: bool, sites: Iterable[OracleSite], executed_ids: set[str]) -> dict[str, bool]:
    executed = {s.oracle_class for s in sites if s.oracle_id in executed_ids}
    return {
        "execution_success": suite_passed,
        "executed_nontrivial_gate": suite_passed and bool(executed & {OracleClass.WEAK, OracleClass.STRONG}),
        "executed_strong_gate": suite_passed and OracleClass.STRONG in executed,
    }
