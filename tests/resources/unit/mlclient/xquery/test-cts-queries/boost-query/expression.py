"""Native boost query serialization and compilation."""

from mlclient.xquery import cts


def run():
    return cts.boost_query(
        cts.collection_query("reports"),
        cts.collection_query("notes"),
    )
