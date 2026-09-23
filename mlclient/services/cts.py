"""Higher-level cts service (CtsService / AsyncCtsService).

Builders compose expressions; services execute through the common evaluator.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mlclient._experimental import experimental
from mlclient.functions.xqy._cts import Cts
from mlclient.functions.xqy._expr import Expr, namespace_bindings
from mlclient.services.eval import AsyncEvalService, EvalService

if TYPE_CHECKING:
    from mlclient.api.rest import AsyncRestApi, RestApi

Range = int | list[int] | tuple[int, int]
_RANGE_BOUND_COUNT = 2


def _ranged(expr: Expr, value: Range | None) -> Expr:
    if value is None:
        return expr
    if type(value) is int:
        return expr.range(1, value)
    if not isinstance(value, (list, tuple)) or len(value) != _RANGE_BOUND_COUNT:
        message = "range must be an integer or a pair of integer positions"
        raise TypeError(message)
    return expr.range(*value)


def _execution_options(default_namespaces: dict[str, str], options: dict) -> dict:
    """Merge per-call namespace overrides without changing service defaults.

    Parameters
    ----------
    default_namespaces : dict[str, str]
        Namespace declarations owned by the CTS service.
    options : dict
        Per-call evaluator options, optionally including namespaces.

    Returns
    -------
    dict
        Independent options with namespace overrides applied by prefix.
    """
    return {
        **options,
        "namespaces": {
            **default_namespaces,
            **namespace_bindings(options.get("namespaces")),
        },
    }


def _single(item):
    """Require the scalar result returned by the estimate convenience method."""
    if isinstance(item, list):
        message = "expected exactly one result item"
        raise TypeError(message)
    return item


@experimental(log_on_init=True)
class CtsService(Cts):
    """Executes cts search, lexicon and estimate queries via ``/v1/eval``."""

    def __init__(self, rest: RestApi, *, namespaces=None):
        """Create search utilities using the client's REST API.

        Parameters
        ----------
        rest : RestApi
            REST API used by the expression evaluator; no request is made here.
        namespaces : dict[str, str] | None
            Default XQuery namespace declarations, copied at construction. The
            empty prefix sets the default element namespace. All execution
            methods accept namespaces overrides through keyword arguments.
        """
        self._namespaces = namespace_bindings(namespaces)
        self._eval = EvalService(rest)

    def search(
        self,
        expression: str | Expr | None = None,
        query: Expr | None = None,
        *,
        options=None,
        quality_weight=None,
        forest_ids=None,
        range: Range | None = None,  # noqa: A002
        **kwargs,
    ) -> object:
        """Run ``cts:search`` and return the parsed nodes.

        Parameters
        ----------
        expression : str | Expr | None
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
        range : int | list[int] | tuple[int, int] | None
            One-based inclusive range: N means (1, N). None leaves the result
            unsliced.
        kwargs : dict
            Execution options: database, txid, output_type, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        object | list
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

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
        return self._eval.expression(
            expr, **_execution_options(self._namespaces, kwargs),
        )

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
    ) -> object:
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
        range : int | list[int] | tuple[int, int] | None
            One-based inclusive range: N means (1, N). None leaves the result
            unsliced.
        kwargs : dict
            Execution options: database, txid, output_type, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        object | list
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

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
        return self._eval.expression(
            expr, **_execution_options(self._namespaces, kwargs),
        )

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
    ) -> object:
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
        range : int | list[int] | tuple[int, int] | None
            One-based inclusive range: N means (1, N). None leaves the result
            unsliced.
        kwargs : dict
            Execution options: database, txid, output_type, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        object | list
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

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
        return self._eval.expression(
            expr, **_execution_options(self._namespaces, kwargs),
        )

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
            Execution options: database, txid, output_type, timeout and namespaces.
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
            self._eval.expression(
                Cts.estimate(
                    query,
                    options=options,
                    quality_weight=quality_weight,
                    forest_ids=forest_ids,
                    maximum=maximum,
                ),
                **_execution_options(self._namespaces, kwargs),
            ),
        )


@experimental(log_on_init=True)
class AsyncCtsService(Cts):
    """Async execution of cts search, lexicon and estimate queries via ``/v1/eval``."""

    def __init__(self, rest: AsyncRestApi, *, namespaces=None):
        """Create async search utilities using the client's REST API.

        Parameters
        ----------
        rest : AsyncRestApi
            REST API used by the expression evaluator; no request is made here.
        namespaces : dict[str, str] | None
            Default XQuery namespace declarations, copied at construction. The
            empty prefix sets the default element namespace. All execution
            methods accept namespaces overrides through keyword arguments.
        """
        self._namespaces = namespace_bindings(namespaces)
        self._eval = AsyncEvalService(rest)

    async def search(
        self,
        expression: str | Expr | None = None,
        query: Expr | None = None,
        *,
        options=None,
        quality_weight=None,
        forest_ids=None,
        range: Range | None = None,  # noqa: A002
        **kwargs,
    ) -> object:
        """Run ``cts:search`` and return the parsed nodes.

        Parameters
        ----------
        expression : str | Expr | None
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
        range : int | list[int] | tuple[int, int] | None
            One-based inclusive range: N means (1, N). None leaves the result
            unsliced.
        kwargs : dict
            Execution options: database, txid, output_type, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        object | list
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

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
        return await self._eval.expression(
            expr, **_execution_options(self._namespaces, kwargs),
        )

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
    ) -> object:
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
        range : int | list[int] | tuple[int, int] | None
            One-based inclusive range: N means (1, N). None leaves the result
            unsliced.
        kwargs : dict
            Execution options: database, txid, output_type, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        object | list
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

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
        return await self._eval.expression(
            expr, **_execution_options(self._namespaces, kwargs),
        )

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
    ) -> object:
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
        range : int | list[int] | tuple[int, int] | None
            One-based inclusive range: N means (1, N). None leaves the result
            unsliced.
        kwargs : dict
            Execution options: database, txid, output_type, timeout and namespaces.
            Unknown names fail.

        Returns
        -------
        object | list
            Empty sequences return []; a singleton returns its item; multiple
            items return a list.

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
        return await self._eval.expression(
            expr, **_execution_options(self._namespaces, kwargs),
        )

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
            Execution options: database, txid, output_type, timeout and namespaces.
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
            await self._eval.expression(
                Cts.estimate(
                    query,
                    options=options,
                    quality_weight=quality_weight,
                    forest_ids=forest_ids,
                    maximum=maximum,
                ),
                **_execution_options(self._namespaces, kwargs),
            ),
        )
