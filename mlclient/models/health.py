"""MarkLogic cluster health representation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClusterHealth:
    """The health verdict of a whole MarkLogic cluster.

    Its truth value is ``healthy``, so ``if ml.cluster_healthcheck():`` reads as
    "if the cluster is healthy".

    Attributes
    ----------
    healthy : bool
        True when every host of the cluster is healthy
    hosts : dict[str, bool] | None
        Health of each host keyed by its MarkLogic host name, or None when the
        verdict comes from the Management API health check, which reports the
        cluster as seen from a single host without a per-host breakdown
    """

    healthy: bool
    hosts: dict[str, bool] | None

    def __bool__(self) -> bool:
        """Return the cluster health verdict."""
        return self.healthy
