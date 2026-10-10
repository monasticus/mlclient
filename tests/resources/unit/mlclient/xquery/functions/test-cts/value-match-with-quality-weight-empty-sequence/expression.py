from mlclient.xquery import cts


def run():
    return cts.value_match(
        cts.element_reference("price"), "prod*", quality_weight=None,
    ).compile()
