from mlclient.xquery import cts


def run():
    return cts.valid_extract_path("/p:item", map=None).compile()
