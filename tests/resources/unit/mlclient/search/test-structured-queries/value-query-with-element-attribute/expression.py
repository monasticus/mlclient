from mlclient.search.structured import Attribute, Element, ValueQuery


def run():
    return ValueQuery(Element("label"), "blue", attribute=Attribute("color"))
