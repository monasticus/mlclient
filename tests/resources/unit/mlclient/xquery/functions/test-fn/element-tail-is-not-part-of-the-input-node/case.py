from xml.etree.ElementTree import fromstring
from mlclient.xquery import fn


def run():
    element = fromstring("<report>blue</report>")
    element.tail = "outside"
    assert fn.data(element).compile()[1]["v0"] == "<report>blue</report>"
    assert element.tail == "outside"
