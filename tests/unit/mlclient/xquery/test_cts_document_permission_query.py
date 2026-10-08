"""Serialization through the public CTS builder.

Native constructor: ``cts:document-permission-query``.
"""

from xml.etree.ElementTree import tostring

from mlclient.xquery import DocumentPermissionQuery, cts


def test_document_permission_query():
    query = cts.document_permission_query("admin", "read")
    assert isinstance(query, DocumentPermissionQuery)
    assert query.serialize() == {
        "documentPermissionQuery": {"role": "admin", "capability": "read"},
    }
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:document-permission-query xmlns:cts="http://marklogic.com/cts" role'
        '="admin" capability="read" />'
    )
