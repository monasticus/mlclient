from mlclient.search.options import WordConstraint
from mlclient.search.structured import Element


def run():
    return WordConstraint("title", Element("title"))
