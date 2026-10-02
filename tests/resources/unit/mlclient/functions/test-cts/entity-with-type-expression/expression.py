from mlclient.functions.xqy import cts, fn


def run():
    return cts.entity(
        "id", "normalized-text", "MarkLogic search", fn.string(cts.search().pos(1)),
    ).compile()
