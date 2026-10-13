from mlclient.xquery import cts, fn


def run():
    return cts.value_match(
        cts.element_reference("price"),
        "prod*",
        quality_weight=fn.count(cts.search().pos(1)),
    ).compile()
