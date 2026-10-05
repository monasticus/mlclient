from mlclient.functions.xqy import cts


def run():
    return cts.stem("MarkLogic search", part_of_speech="noun").compile()
