from mlclient.functions.xqy import cts


def run():
    return cts.word_match("prod*", quality_weight=2.5).compile()
