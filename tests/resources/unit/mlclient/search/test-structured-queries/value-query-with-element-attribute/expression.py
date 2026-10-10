from mlclient.search.structured import Element
from mlclient.search.structured import Attribute, ValueQuery


def run():
    return ValueQuery(Element("label"), "blue", attribute=Attribute("color"))
