from mlclient.xquery import cts


def run():
    return cts.value_match(
        cts.element_reference("price"), "prod*", forest_ids=None,
    ).compile()
