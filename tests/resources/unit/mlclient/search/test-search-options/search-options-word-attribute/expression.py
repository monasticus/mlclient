from mlclient.search.options import SearchOptions, WordConstraint
from mlclient.search.structured import Attribute, Element


def run():
    return SearchOptions(
        WordConstraint("code", Element("item"), attribute=Attribute("code")),
    )
