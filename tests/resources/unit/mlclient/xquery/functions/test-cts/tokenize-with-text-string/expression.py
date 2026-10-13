from mlclient.xquery import cts


def run():
    return cts.tokenize("MarkLogic search").compile()
