from mlclient.search.structured import Field, WordQuery


def run():
    return WordQuery(Field("title"), "blue")
