"""Arguments that CTS queries cannot serialize locally are rejected explicitly."""

from mlclient.xquery import cts


def run():
    return cts.document_format_query(["json", "xml"]).serialize()
