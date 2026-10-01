from mlclient.functions.xqy import cts, fn


def run():
    return cts.stem(
        "MarkLogic search", language=fn.string(cts.search().index(1)),
    ).compile()
