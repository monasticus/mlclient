"""Higher-level cts service (CtsService / AsyncCtsService).

Builders compose expressions; services execute through the common evaluator.
"""

from __future__ import annotations

from mlclient._experimental import experimental
from mlclient.functions.xqy._cts import Cts
from mlclient.functions.xqy._expr import Expr
from mlclient.services._executor import _AsyncExecutor, _SyncExecutor, _single

Range = int | tuple[int, int]
_RANGE_BOUND_COUNT = 2


def _ranged(expr: Expr, value: Range | None) -> Expr:
    if value is None:
        return expr
    if type(value) is int:
        return expr.window(1, value)
    if not isinstance(value, tuple) or len(value) != _RANGE_BOUND_COUNT:
        message = "range must be an integer or a pair of integer positions"
        raise TypeError(message)
    return expr.window(*value)


@experimental(log_on_init=True)
class CtsService(_SyncExecutor):
    """Executes cts search, lexicon and estimate queries via ``/v1/eval``."""

    def search(
        self,
        expression: Expr | None = None,
        query: Expr | None = None,
        *,
        options=None,
        quality_weight=None,
        forest_ids=None,
        range: Range | None = None,  # noqa: A002
        **kwargs,
    ) -> list:
        """Run ``cts:search`` and return the parsed nodes.

        Parameters
        ----------
        expression : Expr | None
            Searchable node expression; None uses /. Wrap trusted source in
            xpath.
        query : Expr | str | None
            Native query expression; None supplies an empty query slot.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | Expr | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | Expr | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.
        range : int | tuple[int, int] | None
            One-based inclusive window: N means (1, N). None leaves the result
            unsliced.
        kwargs : dict
            Execution options: database, txid, output_type and timeout only.
            Unknown names fail.

        Returns
        -------
        list
            One entry per result item, including zero or one item.

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        expr = _ranged(
            Cts.search(
                expression,
                query,
                options=options,
                quality_weight=quality_weight,
                forest_ids=forest_ids,
            ),
            range,
        )
        return self._evaluate(expr, **kwargs)

    def uris(
        self,
        query: Expr | None = None,
        *,
        start=None,
        options=None,
        quality_weight=None,
        forest_ids=None,
        range: Range | None = None,  # noqa: A002
        **kwargs,
    ) -> list:
        """Run ``cts:uris`` and return the matching URIs; ``range`` slices lazily.

        Parameters
        ----------
        query : Expr | str | None
            Native query expression; None supplies an empty query slot.
        start : object
            Optional starting lexicon value. Its type must match the lexicon.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | Expr | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | Expr | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.
        range : int | tuple[int, int] | None
            One-based inclusive window: N means (1, N). None leaves the result
            unsliced.
        kwargs : dict
            Execution options: database, txid, output_type and timeout only.
            Unknown names fail.

        Returns
        -------
        list
            One entry per result item, including zero or one item.

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        expr = _ranged(
            Cts.uris(
                query,
                start=start,
                options=options,
                quality_weight=quality_weight,
                forest_ids=forest_ids,
            ),
            range,
        )
        return self._evaluate(expr, **kwargs)

    def values(
        self,
        references,
        query: Expr | None = None,
        *,
        start=None,
        options=None,
        quality_weight=None,
        forest_ids=None,
        range: Range | None = None,  # noqa: A002
        **kwargs,
    ) -> list:
        """Run ``cts:values`` and return the lexicon values.

        Parameters
        ----------
        references : Expr | list | tuple
            One or more native range-index reference expressions.
        query : Expr | str | None
            Native query expression; None supplies an empty query slot.
        start : object
            Optional starting lexicon value. Its type must match the lexicon.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | Expr | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | Expr | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.
        range : int | tuple[int, int] | None
            One-based inclusive window: N means (1, N). None leaves the result
            unsliced.
        kwargs : dict
            Execution options: database, txid, output_type and timeout only.
            Unknown names fail.

        Returns
        -------
        list
            One entry per result item, including zero or one item.

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        expr = _ranged(
            Cts.values(
                references,
                query,
                start=start,
                options=options,
                quality_weight=quality_weight,
                forest_ids=forest_ids,
            ),
            range,
        )
        return self._evaluate(expr, **kwargs)

    def estimate(
        self,
        query: Expr | None = None,
        *,
        options=None,
        quality_weight=None,
        forest_ids=None,
        maximum=None,
        **kwargs,
    ) -> int | str | bytes:
        """Run ``cts:estimate`` and return the fragment count.

        Parameters
        ----------
        query : Expr | str | None
            Native query expression; None supplies an empty query slot.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | Expr | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | Expr | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.
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
            self._evaluate(
                Cts.estimate(
                    query,
                    options=options,
                    quality_weight=quality_weight,
                    forest_ids=forest_ids,
                    maximum=maximum,
                ),
                **kwargs,
            ),
        )


@experimental(log_on_init=True)
class AsyncCtsService(_AsyncExecutor):
    """Async execution of cts search, lexicon and estimate queries via ``/v1/eval``."""

    async def search(
        self,
        expression: Expr | None = None,
        query: Expr | None = None,
        *,
        options=None,
        quality_weight=None,
        forest_ids=None,
        range: Range | None = None,  # noqa: A002
        **kwargs,
    ) -> list:
        """Run ``cts:search`` and return the parsed nodes.

        Parameters
        ----------
        expression : Expr | None
            Searchable node expression; None uses /. Wrap trusted source in
            xpath.
        query : Expr | str | None
            Native query expression; None supplies an empty query slot.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | Expr | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | Expr | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.
        range : int | tuple[int, int] | None
            One-based inclusive window: N means (1, N). None leaves the result
            unsliced.
        kwargs : dict
            Execution options: database, txid, output_type and timeout only.
            Unknown names fail.

        Returns
        -------
        list
            One entry per result item, including zero or one item.

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        expr = _ranged(
            Cts.search(
                expression,
                query,
                options=options,
                quality_weight=quality_weight,
                forest_ids=forest_ids,
            ),
            range,
        )
        return await self._evaluate(expr, **kwargs)

    async def uris(
        self,
        query: Expr | None = None,
        *,
        start=None,
        options=None,
        quality_weight=None,
        forest_ids=None,
        range: Range | None = None,  # noqa: A002
        **kwargs,
    ) -> list:
        """Run ``cts:uris`` and return the matching URIs; ``range`` slices lazily.

        Parameters
        ----------
        query : Expr | str | None
            Native query expression; None supplies an empty query slot.
        start : object
            Optional starting lexicon value. Its type must match the lexicon.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | Expr | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | Expr | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.
        range : int | tuple[int, int] | None
            One-based inclusive window: N means (1, N). None leaves the result
            unsliced.
        kwargs : dict
            Execution options: database, txid, output_type and timeout only.
            Unknown names fail.

        Returns
        -------
        list
            One entry per result item, including zero or one item.

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        expr = _ranged(
            Cts.uris(
                query,
                start=start,
                options=options,
                quality_weight=quality_weight,
                forest_ids=forest_ids,
            ),
            range,
        )
        return await self._evaluate(expr, **kwargs)

    async def values(
        self,
        references,
        query: Expr | None = None,
        *,
        start=None,
        options=None,
        quality_weight=None,
        forest_ids=None,
        range: Range | None = None,  # noqa: A002
        **kwargs,
    ) -> list:
        """Run ``cts:values`` and return the lexicon values.

        Parameters
        ----------
        references : Expr | list | tuple
            One or more native range-index reference expressions.
        query : Expr | str | None
            Native query expression; None supplies an empty query slot.
        start : object
            Optional starting lexicon value. Its type must match the lexicon.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | Expr | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | Expr | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.
        range : int | tuple[int, int] | None
            One-based inclusive window: N means (1, N). None leaves the result
            unsliced.
        kwargs : dict
            Execution options: database, txid, output_type and timeout only.
            Unknown names fail.

        Returns
        -------
        list
            One entry per result item, including zero or one item.

        Raises
        ------
        TypeError
            For an unknown execution keyword or invalid input type.
        MarkLogicError
            For a server error, including missing indexes or unsupported functions.
        """
        expr = _ranged(
            Cts.values(
                references,
                query,
                start=start,
                options=options,
                quality_weight=quality_weight,
                forest_ids=forest_ids,
            ),
            range,
        )
        return await self._evaluate(expr, **kwargs)

    async def estimate(
        self,
        query: Expr | None = None,
        *,
        options=None,
        quality_weight=None,
        forest_ids=None,
        maximum=None,
        **kwargs,
    ) -> int | str | bytes:
        """Run ``cts:estimate`` and return the fragment count.

        Parameters
        ----------
        query : Expr | str | None
            Native query expression; None supplies an empty query slot.
        options : str | Expr | list | tuple | None
            Native options. None omits the slot; an empty list passes ().
        quality_weight : int | float | Expr | None
            Document quality scoring weight, cast to xs:double.
        forest_ids : int | Expr | list | tuple | None
            Native forest IDs; empty or omitted means all forests in the
            database.
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
            await self._evaluate(
                Cts.estimate(
                    query,
                    options=options,
                    quality_weight=quality_weight,
                    forest_ids=forest_ids,
                    maximum=maximum,
                ),
                **kwargs,
            ),
        )
