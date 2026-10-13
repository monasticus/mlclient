from mlclient.xquery import cts


def run():
    return cts.stem("MarkLogic search", language="en", part_of_speech="noun").compile()
