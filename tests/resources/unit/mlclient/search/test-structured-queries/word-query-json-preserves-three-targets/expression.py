from mlclient.search.structured import Element
from mlclient.search.structured import WordQuery


def run():
    return WordQuery([Element("title"), Element("label"), Element("body")], "blue")
