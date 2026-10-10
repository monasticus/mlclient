from mlclient.xquery import cts


def run():
    return cts.json_property_child_geospatial_query(
        "price", set(), cts.box(10, 10, 20, 20),
    )
