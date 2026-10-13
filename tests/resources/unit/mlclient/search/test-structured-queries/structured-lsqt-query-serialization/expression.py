"""Test LsqtQuery through its public API."""

from mlclient.search.structured import LsqtQuery


def run():
    return LsqtQuery(
        "reports",
        timestamp="2024-01-01T00:00:00Z",
        options=["cached-incremental"],
        weight=2,
    )
