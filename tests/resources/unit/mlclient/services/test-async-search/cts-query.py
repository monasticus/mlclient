from mlclient.xquery import cts


def build():
    return cts.and_query([cts.collection_query("products"), cts.word_query("coffee")])
