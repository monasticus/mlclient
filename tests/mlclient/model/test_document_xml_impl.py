from xml.etree.ElementTree import Element, ElementTree, SubElement

from mlclient.model import Document, DocumentType, XMLDocument


def test_is_document_subclass():
    assert issubclass(XMLDocument, Document)


def test_content():
    root = Element("root")
    parent = SubElement(root, "parent")
    parent.text = "data"

    root.append(parent)
    tree = ElementTree(root)

    document = XMLDocument(tree)
    assert document.content == tree


def test_doc_type():
    assert XMLDocument(ElementTree(Element("root"))).doc_type == DocumentType.XML
