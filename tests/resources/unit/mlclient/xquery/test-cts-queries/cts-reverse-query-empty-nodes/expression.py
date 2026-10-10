"""Public compilation and native serialization of ReverseQuery."""

from mlclient.xquery import cts


def run():
    return cts.reverse_query(None)
