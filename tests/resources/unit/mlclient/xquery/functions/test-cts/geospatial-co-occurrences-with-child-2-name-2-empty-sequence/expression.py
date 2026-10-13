from mlclient.xquery import cts


def run():
    return cts.geospatial_co_occurrences("item", "item", child_2_name_2=None).compile()
