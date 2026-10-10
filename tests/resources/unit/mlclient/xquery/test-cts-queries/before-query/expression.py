"""Native ``cts:before-query`` serialization through the public CTS builder."""

from mlclient.xquery import cts


def run():
    return cts.before_query(16000000000)
