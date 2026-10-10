from mlclient.xquery import cts


def run():
    return cts.valid_document_patch_path("/p:item", map=None).compile()
