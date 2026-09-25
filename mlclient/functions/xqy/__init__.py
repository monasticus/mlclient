"""Public XQuery function builders and ready-to-use namespace singletons.

Import cts, fn, xdmp and xs from this namespace and execute composed
expressions with ml.eval.expression.
"""

from mlclient._experimental import EXPERIMENTAL_NOTICE
from mlclient.functions.xqy._cts import Cts
from mlclient.functions.xqy.expressions import (
    CompilationContext,
    Expression,
    namespace_bindings,
    xpath,
)
from mlclient.functions.xqy._fn import Fn
from mlclient.functions.xqy._xdmp import Xdmp
from mlclient.functions.xqy._xs import Xs

cts = Cts()
fn = Fn()
xdmp = Xdmp()
xs = Xs()

__experimental__ = EXPERIMENTAL_NOTICE

__all__ = [
    "CompilationContext",
    "Cts",
    "Expression",
    "Fn",
    "Xdmp",
    "Xs",
    "cts",
    "fn",
    "namespace_bindings",
    "xdmp",
    "xpath",
    "xs",
]
