from mlclient.functions.xqy import cts


def run():
    return cts.geospatial_co_occurrences("item", "item", child_1_name_2=None).compile()
