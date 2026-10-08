from mlclient.xquery import cts, fn


def run():
    return cts.value_match(
        cts.element_reference("price"),
        "prod*",
        options=[fn.string(cts.search().pos(1)), fn.string(cts.search().pos(2))],
    ).compile()
