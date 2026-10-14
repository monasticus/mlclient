"""Immutable contexts for document, evaluation and search services."""

from __future__ import annotations

import copy
from dataclasses import dataclass, fields, replace

from mlclient._options import UNSET
from mlclient.search.options import SearchOptions


@dataclass(frozen=True)
class ServiceScope:
    """Immutable defaults for document operations and code evaluation.

    Parameters
    ----------
    database : str | None, default unset
        Content database. Unset inherits; None clears an inherited value.
    txid : str | None, default unset
        Transaction identifier. Unset inherits; None clears an inherited value.
    """

    database: str | None = UNSET
    txid: str | None = UNSET

    def overridden_by(self, other: ServiceScope | None) -> ServiceScope:
        """Return a scope with the explicitly supplied fields overridden.

        Parameters
        ----------
        other : ServiceScope | None
            Overrides; omitted fields inherit. None leaves this scope unchanged.

        Returns
        -------
        ServiceScope
            The merged, immutable scope.

        Raises
        ------
        TypeError
            If other is neither a ServiceScope nor None.
        """
        if other is None:
            return self
        if not isinstance(other, ServiceScope):
            message = f"scope must be a ServiceScope, got {type(other).__name__}"
            raise TypeError(message)
        overrides = {
            name: value
            for name, value in (("database", other.database), ("txid", other.txid))
            if value is not UNSET
        }
        return replace(self, **overrides)

    def request_params(self) -> dict:
        """Return database and transaction endpoint arguments.

        Returns
        -------
        dict
            Unset fields resolve to None, selecting the server's defaults.
        """
        return {
            "database": None if self.database is UNSET else self.database,
            "txid": None if self.txid is UNSET else self.txid,
        }


OptionsInput = str | dict | SearchOptions | None
"""Installed options name, native inline options members, or an options builder."""


@dataclass(frozen=True)
class SearchScope:
    """Where searches run and which search options apply.

    Every field defaults to unset, meaning inherited: a scope passed to one
    operation overrides only the fields it sets on its service's scope, and
    None explicitly clears an inherited value. A TransactionService unpacks
    into it: ``SearchScope(**txn)``.

    Parameters
    ----------
    database : str | None, default unset
        Content database name or id; None uses the REST server's database.
    txid : str | None, default unset
        Multi-statement transaction to search within.
    collection : str | list[str] | None, default unset
        Restrict matches to one or more OR-related collections.
    directory : str | None, default unset
        Restrict matches to this database directory.
    forest_name : str | list[str] | None, default unset
        Restrict matches to these database forests.
    options : str | dict | SearchOptions | None, default unset
        Installed options name, or inline options members or builder sent in
        the combined query. Inline options do not install configuration; a
        dict is copied, so later changes to it do not affect the scope.
    timestamp : str | None, default unset
        Effective timestamp from an earlier response, for snapshot pagination.

    Raises
    ------
    TypeError
        If options are not a name, dict or SearchOptions, or a dict wraps its
        members in an ``options`` key.
    """

    database: str | None = UNSET
    txid: str | None = UNSET
    collection: str | list[str] | None = UNSET
    directory: str | None = UNSET
    forest_name: str | list[str] | None = UNSET
    options: OptionsInput = UNSET
    timestamp: str | None = UNSET

    def __post_init__(self):
        """Freeze list restrictions to tuples and copy inline options.

        Raises
        ------
        TypeError
            If options are not a name, dict or SearchOptions, or a dict wraps
            its members in an ``options`` key.
        """
        for name in ("collection", "forest_name"):
            if isinstance(getattr(self, name), list):
                object.__setattr__(self, name, tuple(getattr(self, name)))
        if isinstance(self.options, dict):
            _check_inline_options(self.options)
            object.__setattr__(self, "options", copy.deepcopy(self.options))
        elif not isinstance(self.options, (str, SearchOptions)) and (
            self.options is not UNSET and self.options is not None
        ):
            message = (
                "options must be an installed name, inline dictionary or "
                f"SearchOptions, got {type(self.options).__name__}"
            )
            raise TypeError(message)

    def overridden_by(self, other: SearchScope | None) -> SearchScope:
        """Return this scope with every field another scope sets.

        Parameters
        ----------
        other : SearchScope | None
            The overriding scope; None overrides nothing.

        Returns
        -------
        SearchScope
            A new scope; fields unset in other keep this scope's values.

        Raises
        ------
        TypeError
            If other is neither a SearchScope nor None.
        """
        if other is None:
            return self
        if not isinstance(other, SearchScope):
            message = f"scope must be a SearchScope, got {type(other).__name__}"
            raise TypeError(message)
        overrides = {
            field.name: getattr(other, field.name)
            for field in fields(other)
            if getattr(other, field.name) is not UNSET
        }
        return replace(self, **overrides)

    def request_params(self) -> dict:
        """Return the endpoint arguments of every set field except options.

        Options are not a plain argument: installed names are sent as a query
        parameter and inline options in a combined-query body.

        Returns
        -------
        dict
            Endpoint keyword arguments; unset fields are omitted.
        """
        return {
            field.name: getattr(self, field.name)
            for field in fields(self)
            if field.name != "options" and getattr(self, field.name) is not UNSET
        }


def _check_inline_options(options: dict):
    """Reject inline options still wrapped in their ``options`` object.

    Parameters
    ----------
    options : dict
        Inline options members, as the combined query's options member.

    Raises
    ------
    TypeError
        If the only member is ``options``, which is not a search option.
    """
    if options.keys() == {"options"}:
        message = (
            "inline options must be the members of the options object; "
            "pass options['options'] instead of the whole object"
        )
        raise TypeError(message)
