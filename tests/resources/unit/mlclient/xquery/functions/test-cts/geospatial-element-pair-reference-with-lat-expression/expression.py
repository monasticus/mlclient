from mlclient.xquery import cts, fn


def run():
    return cts.geospatial_element_pair_reference(
        "item", fn.string(cts.search().pos(1)), "longitude",
    ).compile()
