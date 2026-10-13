from mlclient.xquery import cts, fn


def run():
    return cts.element_pair_geospatial_value_match(
        "item",
        "latitude",
        "longitude",
        "prod*",
        options=fn.string(cts.search().pos(1)),
    ).compile()
