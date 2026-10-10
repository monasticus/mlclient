from mlclient.xquery import cts, fn


def run():
    return cts.entity(
        fn.string(cts.search().pos(1)), "normalized-text", "MarkLogic search", "type",
    ).compile()
