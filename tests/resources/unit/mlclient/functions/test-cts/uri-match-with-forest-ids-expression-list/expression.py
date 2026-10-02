from mlclient.functions.xqy import cts, fn


def run():
    return cts.uri_match(
        "prod*",
        forest_ids=[fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))],
    ).compile()
