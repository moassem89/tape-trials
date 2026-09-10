"""AST checks the generator must not be trusted to satisfy on its own.

The same-variable binary-operand rule is the important one. The pilot measured what the
toolchain does when a variable appears on both sides of a binary operator: `a + a`
returns `a`, contradicting the documented meaning of `+`, and `a == a` and `b && b` are
outright nondeterministic across repeats. A single such expression anywhere in a program
makes its answer key either wrong or unstable, and the failure is silent.

Checking the generated AST rather than the template code means a future template can
introduce the pattern and still be caught. `array_access` operands are exempt: each
access lowers to a fresh temporary, so `ar[i] + ar[j]` and even `ar[i] + ar[i]` do not
collapse.
"""

from __future__ import annotations

from ampliphi.ast_nodes import (
    ArrayAccessNode,
    BinaryOperationNode,
    IdentifierNode,
    IfStatementNode,
    ProgramNode,
    UnaryOperationNode,
    WhileStatementNode,
)
from ampliphi.utils import get_ast


def _expressions(node) -> list:
    """Every expression reachable from a statement, flattened."""
    out = []
    if isinstance(node, (IfStatementNode,)):
        for s in list(node.then_block) + list(node.else_block):
            out += _expressions(s)
    elif isinstance(node, WhileStatementNode):
        for s in node.body:
            out += _expressions(s)
    elif hasattr(node, "expression"):
        out.append(node.expression)
    return out


def _walk(expr) -> list:
    if isinstance(expr, BinaryOperationNode):
        return [expr] + _walk(expr.left) + _walk(expr.right)
    if isinstance(expr, UnaryOperationNode):
        return _walk(expr.operand)
    if isinstance(expr, ArrayAccessNode):
        return _walk(expr.index)
    return []


def check(source: str) -> list[str]:
    """Return a list of violations. Empty means the program passes."""
    ast: ProgramNode = get_ast(source)
    problems: list[str] = []

    exprs = []
    for proc in ast.procedures:
        for stmt in proc.statements:
            exprs += _expressions(stmt)

    for expr in exprs:
        for binop in _walk(expr):
            left, right = binop.left, binop.right
            if isinstance(left, IdentifierNode) and isinstance(right, IdentifierNode):
                if left.contents == right.contents:
                    problems.append(f"same-variable binary operands: {left.contents} {binop.op.value} {right.contents}")

    names = {p.name.contents for p in ast.procedures}
    if "main" not in names:
        problems.append("no main procedure")

    return problems
