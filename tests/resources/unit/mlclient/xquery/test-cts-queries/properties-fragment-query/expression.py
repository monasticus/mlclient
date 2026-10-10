"""Native properties fragment query serialization and compilation."""

from mlclient.xquery import cts


def run():
    return cts.properties_fragment_query(cts.collection_query("reports"))
