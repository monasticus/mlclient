from mlclient.xquery import cts


def run():
    return cts.valid_tde_context("/p:item", map=None).compile()
