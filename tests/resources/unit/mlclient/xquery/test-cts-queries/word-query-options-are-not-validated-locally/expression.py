from mlclient.xquery import cts


def run():
    return cts.word_query("blue", options=["lang=eng", "synonym", "synonym", "bogus"])
