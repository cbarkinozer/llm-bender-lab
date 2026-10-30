"""Neutral verification facade; preserve valid module headers during instrumentation.

The original paper checkout stays unchanged. This adapter repairs header placement
for the demo reference rather than altering frozen study sources or results.
"""
import ast
from step4_evaluation.oracle_analysis import OracleClass, classify_oracles, gate_outcomes
from step4_evaluation.oracle_analysis import instrument_oracles as _instrument


def instrument_oracles(source, sut_names=()):
    original=ast.parse(source)
    instrumented,sites=_instrument(source,sut_names=sut_names)
    tree=ast.parse(instrumented)
    doc=(original.body[0].value.value if original.body and isinstance(original.body[0],ast.Expr)
         and isinstance(original.body[0].value,ast.Constant) and isinstance(original.body[0].value.value,str) else None)
    header=[];rest=[]
    for node in tree.body:
        if doc is not None and isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and node.value.value==doc:
            header.insert(0,node)
        elif isinstance(node,ast.ImportFrom) and node.module=='__future__':header.append(node)
        else:rest.append(node)
    tree.body=header+rest
    return ast.unparse(tree),sites
