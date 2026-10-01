from mlclient.functions.xqy import cts, fn


def run():
    return cts.json_property_child_geospatial_query(
        fn.string(cts.search().index(1)), "price", cts.box(10, 10, 20, 20),
    ).compile()
