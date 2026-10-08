from mlclient.xquery import cts, fn


def run():
    return cts.geospatial_co_occurrences(
        "item", "item", options=fn.string(cts.search().pos(1)),
    ).compile()
