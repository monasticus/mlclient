from mlclient.xquery import cts, fn


def run():
    return cts.uri_match(
        "prod*", quality_weight=fn.count(cts.search().pos(1)),
    ).compile()
