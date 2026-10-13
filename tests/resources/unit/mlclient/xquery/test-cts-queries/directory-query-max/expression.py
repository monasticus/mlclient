"""Native directory query serialization and compilation."""

from mlclient.xquery import cts


def run():
    return cts.directory_query(["/reports/", "/notes/"], depth="infinity")
