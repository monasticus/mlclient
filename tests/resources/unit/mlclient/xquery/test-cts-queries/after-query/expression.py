"""Native ``cts:after-query`` serialization through the public CTS builder."""

from mlclient.xquery import cts


def run():
    return cts.after_query(16000000000)
