from mlclient.xquery import cts


def run():
    return cts.json_property_geospatial_query(
        "price", cts.box(10, 10, 20, 20), options="checked", weight=2.5,
    ).compile()
