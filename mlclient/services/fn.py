"""Higher-level fn service (FnService / AsyncFnService).

Both inherit the ``Fn`` builder API and override the aggregating functions to
compile the wrapped expression tree and evaluate it. Wrapping a ``cts:`` builder
lets a single round-trip answer questions like "how many lexicon values match".
"""

from __future__ import annotations

from mlclient._experimental import experimental
from mlclient.functions.xqy._fn import Fn
from mlclient.services._executor import _AsyncExecutor, _SyncExecutor


@experimental(log_on_init=True)
class FnService(Fn, _SyncExecutor):
    """Executes ``fn:`` aggregates over nested expressions via ``/v1/eval``."""

    def count(self, sequence, **kwargs):
        """Run ``fn:count`` and return the size of the sequence."""
        return self._evaluate(super().count(sequence), **kwargs)

    def exists(self, sequence, **kwargs):
        """Run ``fn:exists`` and return whether the sequence is non-empty."""
        return self._evaluate(super().exists(sequence), **kwargs)

    def empty(self, sequence, **kwargs):
        """Run ``fn:empty`` and return whether the sequence is empty."""
        return self._evaluate(super().empty(sequence), **kwargs)


@experimental(log_on_init=True)
class AsyncFnService(Fn, _AsyncExecutor):
    """Async ``fn:`` aggregate execution over nested expressions via ``/v1/eval``."""

    async def count(self, sequence, **kwargs):
        """Run ``fn:count`` and return the size of the sequence."""
        return await self._evaluate(super().count(sequence), **kwargs)

    async def exists(self, sequence, **kwargs):
        """Run ``fn:exists`` and return whether the sequence is non-empty."""
        return await self._evaluate(super().exists(sequence), **kwargs)

    async def empty(self, sequence, **kwargs):
        """Run ``fn:empty`` and return whether the sequence is empty."""
        return await self._evaluate(super().empty(sequence), **kwargs)
