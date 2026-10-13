"""Native not in query serialization and compilation."""

from mlclient.xquery import cts


def run():
    return cts.not_in_query(
        cts.collection_query("reports"),
        cts.collection_query("notes"),
    )
