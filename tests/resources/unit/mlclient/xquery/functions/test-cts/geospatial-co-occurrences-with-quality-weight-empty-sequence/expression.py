from mlclient.xquery import cts


def run():
    return cts.geospatial_co_occurrences("item", "item", quality_weight=None).compile()
