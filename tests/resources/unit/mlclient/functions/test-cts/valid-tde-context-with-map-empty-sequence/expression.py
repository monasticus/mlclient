from mlclient.functions.xqy import cts


def run():
    return cts.valid_tde_context("/p:item", map=None).compile()
