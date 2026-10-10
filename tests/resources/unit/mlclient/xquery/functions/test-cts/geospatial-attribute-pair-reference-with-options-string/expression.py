from mlclient.xquery import cts


def run():
    return cts.geospatial_attribute_pair_reference(
        "item", "latitude", "longitude", options="checked",
    ).compile()
