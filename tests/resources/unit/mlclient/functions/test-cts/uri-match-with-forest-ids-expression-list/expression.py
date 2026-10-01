from mlclient.functions.xqy import cts, fn


def run():
    return cts.uri_match(
        "prod*",
        forest_ids=[fn.count(cts.search().index(1)), fn.count(cts.search().index(2))],
    ).compile()
