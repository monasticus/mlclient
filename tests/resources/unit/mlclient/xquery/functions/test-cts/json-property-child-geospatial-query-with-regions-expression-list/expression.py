from mlclient.xquery import cts


def run():
    return cts.json_property_child_geospatial_query(
        "price", "price", [cts.box(10, 10, 20, 20), cts.box(10, 10, 20, 20)],
    ).compile()
