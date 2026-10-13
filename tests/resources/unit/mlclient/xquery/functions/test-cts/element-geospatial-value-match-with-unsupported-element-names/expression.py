from mlclient.xquery import cts


def run():
    return cts.element_geospatial_value_match(set(), "prod*")
