from mlclient.xquery import cts, fn


def run():
    return cts.element_geospatial_values(
        "item", forest_ids=fn.count(cts.search().pos(1)),
    ).compile()
