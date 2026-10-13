from mlclient.xquery import cts


def run():
    return cts.element_geospatial_boxes("item", latitude_bounds=2.5).compile()
