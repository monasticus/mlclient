from mlclient.functions.xqy import cts


def run():
    return cts.json_property_geospatial_query("price", None).compile()
