"""XQuery function builders (``cts:``, ``xs:``, ``fn:``, ``xdmp:``).

Implementation for the ``mlclient.functions`` public namespace; import the
ready-to-use ``cts``, ``fn``, ``xdmp`` and ``xs`` namespaces from there.
"""

from mlclient.functions.xqy._cts import Cts
from mlclient.functions.xqy._expr import Expr
from mlclient.functions.xqy._fn import Fn
from mlclient.functions.xqy._xdmp import Xdmp
from mlclient.functions.xqy._xs import Xs

cts = Cts()
fn = Fn()
xdmp = Xdmp()
xs = Xs()

__all__ = ["Cts", "Expr", "Fn", "Xdmp", "Xs", "cts", "fn", "xdmp", "xs"]
