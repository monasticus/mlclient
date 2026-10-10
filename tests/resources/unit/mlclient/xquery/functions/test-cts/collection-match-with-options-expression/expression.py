from mlclient.xquery import cts, fn


def run():
    return cts.collection_match(
        "prod*", options=fn.string(cts.search().pos(1)),
    ).compile()
