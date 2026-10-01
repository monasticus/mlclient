from mlclient.functions.xqy import cts, fn


def run():
    return cts.value_match(
        cts.element_reference("price"),
        "prod*",
        options=[fn.string(cts.search().index(1)), fn.string(cts.search().index(2))],
    ).compile()
