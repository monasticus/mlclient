"""Native union query serialization and compilation."""

from mlclient.xquery import cts


def run():
    return cts.or_query([cts.collection_query("reports")], options="synonym")
