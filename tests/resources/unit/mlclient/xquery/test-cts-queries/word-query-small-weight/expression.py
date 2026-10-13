from mlclient.xquery import cts


def run():
    return cts.word_query("blue", weight=1e-05)
