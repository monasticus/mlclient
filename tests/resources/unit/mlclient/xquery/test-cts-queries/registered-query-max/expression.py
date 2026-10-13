"""Native ``cts:registered-query`` serialization through the public CTS builder."""

from mlclient.xquery import cts


def run():
    return cts.registered_query([1, 2], options="unfiltered", weight=2)
