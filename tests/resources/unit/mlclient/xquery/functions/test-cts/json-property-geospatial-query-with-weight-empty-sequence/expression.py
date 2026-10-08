from mlclient.xquery import cts


def run():
    return cts.json_property_geospatial_query(
        "price", cts.box(10, 10, 20, 20), weight=None,
    ).compile()
