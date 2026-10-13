from mlclient.xquery import cts


def run():
    return cts.element_pair_geospatial_value_match("item", set(), "longitude", "prod*")
