from mlclient.xquery import cts


def run():
    return cts.element_pair_geospatial_values(None, "latitude", "longitude").compile()
