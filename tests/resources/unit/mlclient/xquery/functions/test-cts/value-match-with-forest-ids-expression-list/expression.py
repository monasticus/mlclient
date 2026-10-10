from mlclient.xquery import cts, fn


def run():
    return cts.value_match(
        cts.element_reference("price"),
        "prod*",
        forest_ids=[fn.count(cts.search().pos(1)), fn.count(cts.search().pos(2))],
    ).compile()
