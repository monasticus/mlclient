"""Higher-level xdmp service (XdmpService / AsyncXdmpService).

Both inherit the ``Xdmp`` builder API and override the executing functions to
compile the wrapped expression tree and evaluate it.
"""

from __future__ import annotations

from mlclient._experimental import experimental
from mlclient.functions.xqy._xdmp import Xdmp
from mlclient.services._executor import _AsyncExecutor, _SyncExecutor


@experimental(log_on_init=True)
class XdmpService(Xdmp, _SyncExecutor):
    """Executes ``xdmp:`` functions over nested expressions via ``/v1/eval``."""

    def exists(self, searchable, **kwargs):
        """Run ``xdmp:exists`` and return whether anything matches."""
        return self._evaluate(super().exists(searchable), **kwargs)


@experimental(log_on_init=True)
class AsyncXdmpService(Xdmp, _AsyncExecutor):
    """Async ``xdmp:`` execution over nested expressions via ``/v1/eval``."""

    async def exists(self, searchable, **kwargs):
        """Run ``xdmp:exists`` and return whether anything matches."""
        return await self._evaluate(super().exists(searchable), **kwargs)
