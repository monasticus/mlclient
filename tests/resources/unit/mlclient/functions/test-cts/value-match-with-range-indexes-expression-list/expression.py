from mlclient.functions.xqy import cts


def run():
    return cts.value_match(
        [cts.element_reference("price"), cts.element_reference("price")], "prod*",
    ).compile()
