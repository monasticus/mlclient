"""Native document query serialization and compilation."""

from mlclient.xquery import cts


def run():
    return cts.document_query(["/reports/a.xml", "/notes/b.json"])
