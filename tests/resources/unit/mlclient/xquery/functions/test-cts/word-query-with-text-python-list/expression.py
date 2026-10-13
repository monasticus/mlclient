from mlclient.xquery import cts


def run():
    return cts.word_query(["MarkLogic search"]).compile()
