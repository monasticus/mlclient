"""Builders that mirror MarkLogic XQuery function namespaces.

Import ready-to-use namespaces directly::

    from mlclient.functions import cts, fn, xdmp, xs

    query = cts.and_query((cts.directory_query("/some/", "infinity"),
                           cts.document_root("some")))
    hits = fn.count(cts.values(cts.element_reference("mf")))
    any_ = xdmp.exists(cts.search("/reaction", query))

Namespaces here build expression trees for nesting. To execute against
MarkLogic use the matching services in ``mlclient.services`` (``CtsService``,
``FnService``, ``XdmpService``), which share the exact same builder API.
"""

from mlclient.functions.xqy import Cts, Expr, Fn, Xdmp, Xs, cts, fn, xdmp, xs

__experimental__ = Cts.__experimental__

__all__ = ["Cts", "Expr", "Fn", "Xdmp", "Xs", "cts", "fn", "xdmp", "xs"]
