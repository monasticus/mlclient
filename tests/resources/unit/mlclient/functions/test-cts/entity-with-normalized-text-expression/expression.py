from mlclient.functions.xqy import cts, fn


def run():
    return cts.entity(
        "id", fn.string(cts.search().index(1)), "MarkLogic search", "type",
    ).compile()
