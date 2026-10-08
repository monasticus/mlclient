from mlclient.xquery import cts, fn


def run():
    return cts.element_value_match(
        "item", "prod*", options=fn.string(cts.search().pos(1)),
    ).compile()
