"""Serialization through the public CTS builder.

Native constructor: ``cts:document-permission-query``.
"""

from mlclient.xquery import cts


def run():
    return cts.document_permission_query("admin", "read")
