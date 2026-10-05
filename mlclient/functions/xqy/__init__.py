"""Public XQuery function builders and ready-to-use namespace singletons.

Import cts, fn, xdmp and xs from this namespace and execute composed
expressions with ml.eval.expression.
"""

from mlclient.functions.xqy._cts import Cts
from mlclient.functions.xqy._fn import Fn
from mlclient.functions.xqy._xdmp import Xdmp
from mlclient.functions.xqy._xs import Xs
from mlclient.functions.xqy.expressions import (
    AtomicValue,
    DatabaseRoot,
    FunctionCall,
    Index,
    ModuleFunctionCall,
    NamespaceMap,
    Path,
    Range,
    ResultXPath,
    XqyCompilationContext,
    XqyExpression,
    XqySequence,
    as_searchable_expression,
    namespace_bindings,
    xpath,
)

LOCAL_NS_URI = "http://www.w3.org/2005/xquery-local-functions"
"""Namespace URI for XQuery functions and variables with the local prefix."""

cts = Cts()
fn = Fn()
xdmp = Xdmp()
xs = Xs()

__all__ = [
    "LOCAL_NS_URI",
    "AtomicValue",
    "Cts",
    "DatabaseRoot",
    "Fn",
    "FunctionCall",
    "Index",
    "ModuleFunctionCall",
    "NamespaceMap",
    "Path",
    "Range",
    "ResultXPath",
    "Xdmp",
    "XqyCompilationContext",
    "XqyExpression",
    "XqySequence",
    "Xs",
    "as_searchable_expression",
    "cts",
    "fn",
    "namespace_bindings",
    "xdmp",
    "xpath",
    "xs",
]
