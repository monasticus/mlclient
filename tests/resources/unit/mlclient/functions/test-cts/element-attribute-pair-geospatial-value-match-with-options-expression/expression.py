from mlclient.functions.xqy import cts, fn


def run():
    return cts.element_attribute_pair_geospatial_value_match(
        "item",
        "latitude",
        "longitude",
        "prod*",
        options=fn.string(cts.search().pos(1)),
    ).compile()
