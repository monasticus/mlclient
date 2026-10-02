from mlclient.functions.xqy import cts, fn


def run():
    return cts.uri_match(
        "prod*", quality_weight=fn.count(cts.search().pos(1)),
    ).compile()
