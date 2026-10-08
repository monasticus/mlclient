from mlclient.xquery import cts


def run():
    return cts.tokenize(
        "MarkLogic search", language="en", field="description",
    ).compile()
