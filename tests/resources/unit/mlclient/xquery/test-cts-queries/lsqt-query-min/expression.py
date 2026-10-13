"""Native ``cts:lsqt-query`` serialization through the public CTS builder."""

from mlclient.xquery import cts


def run():
    return cts.lsqt_query("temporal")
