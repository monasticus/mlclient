"""Native and not query serialization and compilation."""

from mlclient.xquery import cts


def run():
    return cts.and_not_query(
        cts.collection_query("reports"),
        cts.collection_query("notes"),
    )
