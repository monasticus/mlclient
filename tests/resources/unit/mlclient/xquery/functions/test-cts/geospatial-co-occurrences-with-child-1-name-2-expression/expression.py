from mlclient.xquery import cts, fn


def run():
    return cts.geospatial_co_occurrences(
        "item", "item", child_1_name_2=fn.string(cts.search().pos(1)),
    ).compile()
