from mlclient.search.structured import Element, WordQuery


def run():
    return WordQuery([Element("title"), Element("label"), Element("body")], "blue")
