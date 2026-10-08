from mlclient.xquery import cts


def run():
    return cts.field_reference("description", options="checked").compile()
