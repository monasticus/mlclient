from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_co_occurrences(
        "item", "item", options=fn.string(cts.search().index(1)),
    ).compile()
