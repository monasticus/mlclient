from mlclient.functions.xqy import cts, fn


def run():
    return cts.field_value_match(
        [fn.string(cts.search().index(1)), fn.string(cts.search().index(2))], "prod*",
    ).compile()
