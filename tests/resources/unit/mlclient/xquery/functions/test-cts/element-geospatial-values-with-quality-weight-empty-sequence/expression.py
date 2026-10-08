from mlclient.xquery import cts


def run():
    return cts.element_geospatial_values("item", quality_weight=None).compile()
