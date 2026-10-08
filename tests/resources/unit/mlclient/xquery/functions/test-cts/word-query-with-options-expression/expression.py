from mlclient.xquery import cts, fn


def run():
    return cts.word_query(
        "MarkLogic search", options=fn.string(cts.search().pos(1)),
    ).compile()
