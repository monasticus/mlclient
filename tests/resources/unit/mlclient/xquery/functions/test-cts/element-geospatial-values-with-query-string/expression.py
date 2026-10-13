from mlclient.xquery import cts


def run():
    return cts.element_geospatial_values("item", query="needle").compile()
