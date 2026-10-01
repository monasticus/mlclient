from mlclient.functions.xqy import cts, fn


def run():
    return fn.normalize_unicode(
        "arg", normalization_form=fn.string(cts.search().index(1)),
    ).compile()
