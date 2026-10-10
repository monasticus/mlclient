from mlclient.xquery import cts


def run():
    return cts.json_property_pair_geospatial_query(
        None, "price", "price", cts.box(10, 10, 20, 20),
    ).compile()
