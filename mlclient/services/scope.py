"""Shared database and transaction context for parsed services."""

from __future__ import annotations

from dataclasses import dataclass, replace

from mlclient._options import UNSET


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
