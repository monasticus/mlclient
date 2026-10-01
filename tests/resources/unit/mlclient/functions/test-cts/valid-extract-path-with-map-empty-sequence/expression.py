from mlclient.functions.xqy import cts


def run():
    return cts.valid_extract_path("/p:item", map=None).compile()
