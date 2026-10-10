"""Intersection serialization through the public CTS builder."""

from mlclient.xquery import cts


def run():
    return cts.and_query([], options="bogus")
