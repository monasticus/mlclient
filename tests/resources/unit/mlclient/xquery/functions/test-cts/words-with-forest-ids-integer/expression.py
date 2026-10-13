from mlclient.xquery import cts


def run():
    return cts.words(forest_ids=123).compile()
