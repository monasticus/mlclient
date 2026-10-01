from mlclient.functions.xqy import cts, fn


def run():
    return cts.geospatial_element_pair_reference(
        "item", "latitude", "longitude", options=fn.string(cts.search().index(1)),
    ).compile()
