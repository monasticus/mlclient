from xml.etree.ElementTree import Element, ElementTree, fromstring

import pytest

from mlclient.models import Document, DocumentType, XMLDocument


def test_is_document_subclass():
    assert issubclass(XMLDocument, Document)


def test_content_from_element_tree():
    tree = ElementTree(fromstring("<root><parent>data</parent></root>"))

    document = XMLDocument(tree)
    assert document.content is tree


def test_content_from_element():
    element = fromstring("<root><parent>data</parent></root>")

    document = XMLDocument(element)
    assert isinstance(document.content, ElementTree)
    assert document.content.getroot() is element


def test_content_from_str_lazy_parse():
    xml_str = "<root><parent>data</parent></root>"

    document = XMLDocument(xml_str)
    tree = document.content
    assert isinstance(tree, ElementTree)
    assert tree.getroot().tag == "root"
    assert document.content is tree  # cached


def test_content_from_bytes_lazy_parse():
    xml_bytes = b"<root><parent>data</parent></root>"

    document = XMLDocument(xml_bytes)
    tree = document.content
    assert isinstance(tree, ElementTree)
    assert tree.getroot().tag == "root"
    assert document.content is tree  # cached


def test_content_bytes_from_element_tree():
    tree = ElementTree(fromstring("<root><parent>data</parent></root>"))

    document = XMLDocument(tree)
    assert document.content_bytes == (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><parent>data</parent></root>'
    )


def test_content_bytes_from_str_no_parse():
    invalid_xml = "this is not xml"

    document = XMLDocument(invalid_xml)
    assert document.content_bytes == invalid_xml.encode("utf-8")


def test_content_bytes_from_bytes_zero_copy():
    invalid_xml = b"this is not xml"

    document = XMLDocument(invalid_xml)
    assert document.content_bytes is invalid_xml


def test_content_string_from_element_tree():
    tree = ElementTree(fromstring("<root><parent>data</parent></root>"))

    document = XMLDocument(tree)
    assert document.content_string == (
        '<?xml version="1.0" encoding="UTF-8"?>\n<root><parent>data</parent></root>'
    )


def test_content_string_from_str_zero_copy():
    invalid_xml = "this is not xml"

    document = XMLDocument(invalid_xml)
    assert document.content_string is invalid_xml


def test_content_string_from_bytes_no_parse():
    invalid_xml = b"this is not xml"

    document = XMLDocument(invalid_xml)
    assert document.content_string == "this is not xml"


def test_content_string_from_element_tree_via_bytes():
    tree = ElementTree(fromstring("<root/>"))

    document = XMLDocument(tree)
    assert document.content_string == (
        '<?xml version="1.0" encoding="UTF-8"?>\n<root />'
    )


def test_none_content_raises():
    with pytest.raises(TypeError, match="XMLDocument requires content"):
        XMLDocument(None)


def test_xpath_without_namespaces():
    document = XMLDocument("<patient><name>Smith</name></patient>")

    names = document.xpath("name")
    assert len(names) == 1
    assert names[0].text == "Smith"


def test_xpath_with_namespaces():
    xml = '<med:patient xmlns:med="http://example.com/medical"><med:name>Smith</med:name></med:patient>'
    document = XMLDocument(xml)

    names = document.xpath("med:name", med="http://example.com/medical")
    assert len(names) == 1
    assert names[0].text == "Smith"


def test_invalidate_after_tree_mutation_reserializes():
    document = XMLDocument(b"<root><child>old</child></root>")
    initial = document.content_bytes
    assert b"old" in initial

    document.content.find("child").text = "new"
    chained = document.invalidate()
    assert chained is document
    assert b"new" in document.content_bytes
    assert b"old" not in document.content_bytes


def test_invalidate_without_parsed_keeps_raw():
    raw = b"<root/>"
    document = XMLDocument(raw)
    assert document.invalidate() is document
    assert document.content_bytes is raw


def test_doc_type():
    assert XMLDocument(ElementTree(Element("root"))).doc_type == DocumentType.XML
