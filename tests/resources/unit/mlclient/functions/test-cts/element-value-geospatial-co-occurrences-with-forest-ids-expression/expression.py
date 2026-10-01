from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_value_geospatial_co_occurrences(
        "item", "item", forest_ids=fn.count(cts.search().index(1)),
    ).compile()
