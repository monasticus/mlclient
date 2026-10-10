from xml.etree.ElementTree import (
    Comment,
    ProcessingInstruction,
    SubElement,
    fromstring,
    tostring,
)
from mlclient.xquery import cts


def run():
    root = fromstring(
        '<r:report xmlns:r="urn:reports" xmlns:a="urn:attributes'
        '" a:flag="yes">blue</r:report>',
    )
    root.set("xmlns:node0", "urn:existing-prefix")
    root.append(Comment("retained"))
    root.append(ProcessingInstruction("status", "ready"))
    SubElement(root, "{urn:reports}label").text = "ns0:literal text"
    query = cts.similar_query(root)
    serialized = query.to_xml()
    model = serialized.find("{http://marklogic.com/cts}node")[0]
    assert model.tag == "{urn:reports}report"
    assert model.attrib["{urn:attributes}flag"] == "yes"
    assert model.find("{urn:reports}label").text == "ns0:literal text"
    assert "<!--retained-->" in tostring(serialized, encoding="unicode")
    assert "<?status ready?>" in tostring(serialized, encoding="unicode")
