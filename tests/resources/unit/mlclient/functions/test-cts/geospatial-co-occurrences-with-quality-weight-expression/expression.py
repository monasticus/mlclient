from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_co_occurrences(
        "item", "item", quality_weight=fn.count(cts.search().pos(1)),
    ).compile()
