from mlclient.functions.xqy import cts, fn


def run():
    return cts.valid_document_patch_path(fn.string(cts.search().pos(1))).compile()
