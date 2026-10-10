from mlclient.xquery import cts


def run():
    return cts.match_regions(
        cts.element_reference("price"),
        "operation",
        cts.box(10, 10, 20, 20),
        options="checked",
        query="needle",
        forest_ids=123,
    ).compile()
