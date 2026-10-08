from mlclient.xquery import cts, fn


def run():
    return cts.tokenize(
        "MarkLogic search", language=fn.string(cts.search().pos(1)),
    ).compile()
