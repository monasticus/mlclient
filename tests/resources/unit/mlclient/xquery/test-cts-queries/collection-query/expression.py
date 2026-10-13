"""Collection query serialization and compilation."""

from mlclient.xquery import cts


def run():
    return cts.collection_query(["reports", "notes"])
