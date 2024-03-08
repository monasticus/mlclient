from xml.etree.ElementTree import Element, ElementTree, fromstring

from mlclient.structures import Document, DocumentType, XMLDocument


def test_is_document_subclass():
    assert issubclass(XMLDocument, Document)


def test_content():
    tree = ElementTree(fromstring("<root><parent>data</parent></root>"))

    document = XMLDocument(tree)
    assert document.content == tree


def test_content_bytes():
    tree = ElementTree(fromstring("<root><parent>data</parent></root>"))

    document = XMLDocument(tree)
    assert document.content_bytes == (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<root><parent>data</parent></root>'
    )


def test_content_string():
    tree = ElementTree(fromstring("<root><parent>data</parent></root>"))

    document = XMLDocument(tree)
    assert document.content_string == (
        '<?xml version="1.0" encoding="UTF-8"?>\n<root><parent>data</parent></root>'
    )


def test_doc_type():
    assert XMLDocument(ElementTree(Element("root"))).doc_type == DocumentType.XML
