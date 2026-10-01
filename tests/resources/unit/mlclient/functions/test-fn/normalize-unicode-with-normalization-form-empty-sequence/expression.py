from mlclient.functions.xqy import fn


def run():
    return fn.normalize_unicode("arg", normalization_form=None).compile()
