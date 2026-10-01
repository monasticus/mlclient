from mlclient.functions.xqy import cts


def run():
    return cts.tokenize("MarkLogic search", field="description").compile()
