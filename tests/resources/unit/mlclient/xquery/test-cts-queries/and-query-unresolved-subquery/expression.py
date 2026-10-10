"""Intersection serialization through the public CTS builder."""

from mlclient.xquery import cts, fn


def run():
    return cts.and_query(fn.string("blue")).serialize()
