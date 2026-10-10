"""Test ValueQuery through the public structured-query API."""

from mlclient.search.structured import JsonProperty, ValueQuery


def run():
    return ValueQuery(
        JsonProperty("active"),
        True,
        node_type="boolean",
        options=["exact"],
        weight=2,
        fragment_scope="documents",
    )
