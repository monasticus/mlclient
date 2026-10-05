from mlclient.functions.xqy import cts, fn


def run():
    return cts.entity(
        "id", "normalized-text", fn.string(cts.search().pos(1)), "type",
    ).compile()
