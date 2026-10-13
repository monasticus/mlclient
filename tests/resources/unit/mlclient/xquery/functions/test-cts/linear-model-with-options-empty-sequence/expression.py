from mlclient.xquery import cts


def run():
    return cts.linear_model(cts.search().pos(1), options=None).compile()
