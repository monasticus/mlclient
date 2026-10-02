from mlclient.functions.xqy import cts, fn


def run():
    return fn.normalize_unicode(
        "arg", normalization_form=fn.string(cts.search().pos(1)),
    ).compile()
