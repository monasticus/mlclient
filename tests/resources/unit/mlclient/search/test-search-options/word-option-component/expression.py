from mlclient.search.options import SearchOptions, WordConstraint
from mlclient.search.structured import Element


def run():
    return SearchOptions(WordConstraint("title", Element("title")))
