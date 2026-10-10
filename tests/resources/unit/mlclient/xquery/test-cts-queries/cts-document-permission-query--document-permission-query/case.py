"""Serialization through the public CTS builder.

Native constructor: ``cts:document-permission-query``.
"""

from tests.utils.resources import read_query_expectation
from xml.etree.ElementTree import tostring
from mlclient.xquery import DocumentPermissionQuery, cts


def run():
    query = cts.document_permission_query("admin", "read")
    assert isinstance(query, DocumentPermissionQuery)
    assert query.serialize() == read_query_expectation(__file__, "expected-1.json")
    assert tostring(query.to_xml(), encoding="unicode") == read_query_expectation(
        __file__,
        "expected-2.xml",
    )
