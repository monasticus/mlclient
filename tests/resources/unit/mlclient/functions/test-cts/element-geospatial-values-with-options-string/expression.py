from mlclient.functions.xqy import cts


def run():
    return cts.element_geospatial_values("item", options="checked").compile()
