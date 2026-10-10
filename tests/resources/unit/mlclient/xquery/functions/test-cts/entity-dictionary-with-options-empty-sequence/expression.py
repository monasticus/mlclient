from mlclient.xquery import cts


def run():
    return cts.entity_dictionary(cts.search().pos(1), options=None).compile()
