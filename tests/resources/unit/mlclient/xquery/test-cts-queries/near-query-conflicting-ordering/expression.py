"""Native proximity query serialization and compilation."""

from mlclient.xquery import cts


def run():
    return cts.near_query([], options=["ordered", "unordered"])
