from mlclient.functions.xqy import cts


def run():
    return cts.word_query("MarkLogic search", options="checked", weight=2.5).compile()
