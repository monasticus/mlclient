from mlclient.xquery import cts


def run():
    return cts.element_child_geospatial_boxes("item", "item", forest_ids=set())
