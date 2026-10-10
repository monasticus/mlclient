from mlclient.xquery import cts


def run():
    return cts.element_attribute_pair_geospatial_value_match(
        "item", "latitude", ["longitude"], "prod*",
    ).compile()
