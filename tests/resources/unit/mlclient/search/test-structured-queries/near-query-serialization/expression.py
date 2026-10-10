"""Test NearQuery through the public structured-query API."""

from mlclient.search.structured import NearQuery, TermQuery


def run():
    return NearQuery(
        [TermQuery("blue"), TermQuery("green")],
        distance=3,
        minimum_distance=1,
        distance_weight=2,
        ordered=False,
    )
