from mlclient.functions.xqy import cts, fn


def run():
    return cts.word_match(
        "prod*", quality_weight=fn.count(cts.search().index(1)),
    ).compile()
