from mlclient.xquery import cts


def run():
    return cts.element_geospatial_value_match("item", "prod*", forest_ids=set())
