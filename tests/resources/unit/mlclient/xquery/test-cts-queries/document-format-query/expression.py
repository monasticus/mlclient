"""Native ``cts:document-format-query`` serialization through the public CTS builder."""

from mlclient.xquery import cts


def run():
    return cts.document_format_query("json")
