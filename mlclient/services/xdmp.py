"""Higher-level xdmp service (XdmpService / AsyncXdmpService).

Builders compose expressions; services execute through the common evaluator.
"""

from __future__ import annotations

from mlclient._experimental import experimental
from mlclient.functions.xqy._xdmp import Xdmp
from mlclient.services._executor import _AsyncExecutor, _SyncExecutor, _single


@experimental(log_on_init=True)
class XdmpService(_SyncExecutor):
    """Executes ``xdmp:`` functions over nested expressions via ``/v1/eval``."""

    def exists(self, searchable, **kwargs) -> bool | str | bytes:
        """Run ``xdmp:exists`` and return whether anything matches.

        Parameters
        ----------
        searchable : Expr
            Partially searchable path or cts:search expression; wrap trusted
            source in xpath.
        kwargs : dict
            Execution options: database, txid, output_type and timeout only.
            Unknown names fail.

        Returns
        -------
        bool
            The single native aggregate result (or raw str/bytes with output_type).

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        return _single(self._evaluate(Xdmp.exists(searchable), **kwargs))


@experimental(log_on_init=True)
class AsyncXdmpService(_AsyncExecutor):
    """Async ``xdmp:`` execution over nested expressions via ``/v1/eval``."""

    async def exists(self, searchable, **kwargs) -> bool | str | bytes:
        """Run ``xdmp:exists`` and return whether anything matches.

        Parameters
        ----------
        searchable : Expr
            Partially searchable path or cts:search expression; wrap trusted
            source in xpath.
        kwargs : dict
            Execution options: database, txid, output_type and timeout only.
            Unknown names fail.

        Returns
        -------
        bool
            The single native aggregate result (or raw str/bytes with output_type).

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        return _single(await self._evaluate(Xdmp.exists(searchable), **kwargs))
