from mlclient.xquery import cts


def run():
    return cts.geospatial_co_occurrences("item", "item", options=["checked"]).compile()
