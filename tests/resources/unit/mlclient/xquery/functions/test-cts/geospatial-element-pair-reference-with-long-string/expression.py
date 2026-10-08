from mlclient.xquery import cts


def run():
    return cts.geospatial_element_pair_reference(
        "item", "latitude", "longitude",
    ).compile()
