from mlclient.xquery import cts, fn


def run():
    return cts.geospatial_co_occurrences(
        "item", "item", child_2_name_1=fn.string(cts.search().pos(1)),
    ).compile()
