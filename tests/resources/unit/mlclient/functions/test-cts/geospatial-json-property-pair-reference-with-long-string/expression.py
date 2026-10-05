from mlclient.functions.xqy import cts


def run():
    return cts.geospatial_json_property_pair_reference(
        "price", "latitude", "longitude",
    ).compile()
