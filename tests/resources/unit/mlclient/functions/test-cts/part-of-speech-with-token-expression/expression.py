from mlclient.functions.xqy import cts


def run():
    return cts.part_of_speech(cts.tokenize("running")).compile()
