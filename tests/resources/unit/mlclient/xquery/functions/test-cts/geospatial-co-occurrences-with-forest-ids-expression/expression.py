from mlclient.xquery import cts, fn


def run():
    return cts.geospatial_co_occurrences(
        "item", "item", forest_ids=fn.count(cts.search().pos(1)),
    ).compile()
