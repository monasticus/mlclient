from mlclient.xquery import cts, fn


def run():
    return cts.geospatial_element_pair_reference(
        "item",
        "latitude",
        "longitude",
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
