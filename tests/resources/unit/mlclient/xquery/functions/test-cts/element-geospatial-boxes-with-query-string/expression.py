from mlclient.xquery import cts


def run():
    return cts.element_geospatial_boxes("item", query="needle").compile()
