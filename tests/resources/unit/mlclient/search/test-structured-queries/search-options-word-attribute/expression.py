from mlclient.search.options import SearchOptions
from mlclient.search.structured import Attribute, Element


def run():
    return SearchOptions().word_constraint(
        "code",
        Element("item"),
        attribute=Attribute("code"),
    )
