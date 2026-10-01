from mlclient.functions.xqy import cts


def run():
    return cts.field_reference("description", options="checked").compile()
