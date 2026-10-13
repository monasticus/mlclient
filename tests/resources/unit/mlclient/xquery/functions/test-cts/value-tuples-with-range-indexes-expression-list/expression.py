from mlclient.xquery import cts


def run():
    return cts.value_tuples(
        [cts.element_reference("price"), cts.element_reference("price")],
    ).compile()
