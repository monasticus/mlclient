from mlclient.functions.xqy import cts, fn


def run():
    return cts.json_property_child_geospatial_query(
        "price",
        "price",
        cts.box(10, 10, 20, 20),
        weight=fn.count(cts.search().index(1)),
    ).compile()
