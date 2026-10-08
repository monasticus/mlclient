from mlclient.xquery import cts


def run():
    return cts.stem("MarkLogic search", part_of_speech=None).compile()
