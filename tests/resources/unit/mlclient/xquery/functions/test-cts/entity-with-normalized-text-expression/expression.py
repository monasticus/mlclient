from mlclient.xquery import cts, fn


def run():
    return cts.entity(
        "id", fn.string(cts.search().pos(1)), "MarkLogic search", "type",
    ).compile()
