from mlclient.functions.xqy import cts, fn


def run():
    return cts.word_query(
        "MarkLogic search", weight=fn.count(cts.search().index(1)),
    ).compile()
