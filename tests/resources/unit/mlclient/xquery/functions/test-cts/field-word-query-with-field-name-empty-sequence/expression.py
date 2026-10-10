from mlclient.xquery import cts


def run():
    return cts.field_word_query(None, "MarkLogic search").compile()
