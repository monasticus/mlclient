from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_value_geospatial_co_occurrences(
        "item",
        "id",
        "item",
        forest_ids=[fn.count(cts.search().index(1)), fn.count(cts.search().index(2))],
    ).compile()
