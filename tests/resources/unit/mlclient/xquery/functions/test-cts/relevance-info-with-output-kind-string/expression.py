from mlclient.xquery import cts


def run():
    return cts.relevance_info(output_kind="output-kind").compile()
