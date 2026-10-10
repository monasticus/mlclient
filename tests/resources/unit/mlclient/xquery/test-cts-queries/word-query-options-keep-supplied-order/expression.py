from mlclient.xquery import cts


def run():
    return cts.word_query("blue", options=["unstemmed", "case-insensitive", "lang=en"])
