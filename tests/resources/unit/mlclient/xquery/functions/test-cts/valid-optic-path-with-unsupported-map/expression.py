from mlclient.xquery import cts


def run():
    return cts.valid_optic_path("/p:item", map=set())
