from mlclient.functions.xqy import cts


def run():
    return cts.json_property_pair_geospatial_query(
        "price", "price", None, cts.box(10, 10, 20, 20),
    ).compile()
