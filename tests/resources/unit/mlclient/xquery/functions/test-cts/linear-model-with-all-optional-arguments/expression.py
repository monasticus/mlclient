from mlclient.xquery import cts


def run():
    return cts.linear_model(
        cts.search().pos(1), options="checked", query="needle", forest_ids=123,
    ).compile()
