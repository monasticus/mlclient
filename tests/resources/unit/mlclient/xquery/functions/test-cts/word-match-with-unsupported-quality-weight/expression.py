from mlclient.xquery import cts


def run():
    return cts.word_match("prod*", quality_weight=set())
