from mlclient.xquery import cts


def run():
    return cts.json_property_child_geospatial_query("price", "price", None).compile()
