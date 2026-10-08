from mlclient.xquery import cts


def run():
    return cts.geospatial_co_occurrences("item", "item", child_1_name_1=None).compile()
