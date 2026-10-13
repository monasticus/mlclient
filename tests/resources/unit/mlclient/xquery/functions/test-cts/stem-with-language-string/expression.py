from mlclient.xquery import cts


def run():
    return cts.stem("MarkLogic search", language="en").compile()
