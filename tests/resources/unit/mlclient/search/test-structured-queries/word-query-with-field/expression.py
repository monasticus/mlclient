from mlclient.search.structured import Field
from mlclient.search.structured import WordQuery


def run():
    return WordQuery(Field("title"), "blue")
