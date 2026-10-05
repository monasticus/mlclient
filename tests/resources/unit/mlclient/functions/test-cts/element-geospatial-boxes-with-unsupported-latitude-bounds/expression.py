from mlclient.functions.xqy import cts


def run():
    return cts.element_geospatial_boxes("item", latitude_bounds=set())
