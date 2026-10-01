from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_pair_geospatial_query(
        "item",
        "id",
        "id",
        cts.box(10, 10, 20, 20),
        weight=fn.count(cts.search().index(1)),
    ).compile()
