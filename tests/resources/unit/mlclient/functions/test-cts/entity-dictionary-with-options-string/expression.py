from mlclient.functions.xqy import cts


def run():
    return cts.entity_dictionary(cts.search().pos(1), options="checked").compile()
