"""Higher-level fn service (FnService / AsyncFnService).

Builders compose expressions; services execute through the common evaluator.
"""

from __future__ import annotations

from mlclient._experimental import experimental
from mlclient.functions.xqy._fn import Fn
from mlclient.services._executor import _AsyncExecutor, _SyncExecutor, _single


@experimental(log_on_init=True)
class FnService(_SyncExecutor):
    """Executes ``fn:`` aggregates over nested expressions via ``/v1/eval``."""

    def count(self, sequence, *, maximum=None, **kwargs) -> int | str | bytes:
        """Run ``fn:count`` and return the size of the sequence.

        Parameters
        ----------
        sequence : object
            Expression or supported Python values; lists/tuples become XQuery
            sequences.
        maximum : int | float | Expr | None
            Native maximum count; None leaves the count uncapped.
        kwargs : dict
            Execution options: database, txid, output_type and timeout only.
            Unknown names fail.

        Returns
        -------
        int
            The single native aggregate result (or raw str/bytes with output_type).

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        return _single(self._evaluate(Fn.count(sequence, maximum=maximum), **kwargs))

    def exists(self, sequence, **kwargs) -> bool | str | bytes:
        """Run ``fn:exists`` and return whether the sequence is non-empty.

        Parameters
        ----------
        sequence : object
            Expression or supported Python values; lists/tuples become XQuery
            sequences.
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
        return _single(self._evaluate(Fn.exists(sequence), **kwargs))

    def empty(self, sequence, **kwargs) -> bool | str | bytes:
        """Run ``fn:empty`` and return whether the sequence is empty.

        Parameters
        ----------
        sequence : object
            Expression or supported Python values; lists/tuples become XQuery
            sequences.
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
        return _single(self._evaluate(Fn.empty(sequence), **kwargs))


@experimental(log_on_init=True)
class AsyncFnService(_AsyncExecutor):
    """Async ``fn:`` aggregate execution over nested expressions via ``/v1/eval``."""

    async def count(self, sequence, *, maximum=None, **kwargs) -> int | str | bytes:
        """Run ``fn:count`` and return the size of the sequence.

        Parameters
        ----------
        sequence : object
            Expression or supported Python values; lists/tuples become XQuery
            sequences.
        maximum : int | float | Expr | None
            Native maximum count; None leaves the count uncapped.
        kwargs : dict
            Execution options: database, txid, output_type and timeout only.
            Unknown names fail.

        Returns
        -------
        int
            The single native aggregate result (or raw str/bytes with output_type).

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        return _single(
            await self._evaluate(Fn.count(sequence, maximum=maximum), **kwargs),
        )

    async def exists(self, sequence, **kwargs) -> bool | str | bytes:
        """Run ``fn:exists`` and return whether the sequence is non-empty.

        Parameters
        ----------
        sequence : object
            Expression or supported Python values; lists/tuples become XQuery
            sequences.
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
        return _single(await self._evaluate(Fn.exists(sequence), **kwargs))

    async def empty(self, sequence, **kwargs) -> bool | str | bytes:
        """Run ``fn:empty`` and return whether the sequence is empty.

        Parameters
        ----------
        sequence : object
            Expression or supported Python values; lists/tuples become XQuery
            sequences.
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
        return _single(await self._evaluate(Fn.empty(sequence), **kwargs))
