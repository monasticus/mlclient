from mlclient.functions.xqy import cts, fn


def run():
    return cts.stem(
        "MarkLogic search", part_of_speech=fn.string(cts.search().index(1)),
    ).compile()
