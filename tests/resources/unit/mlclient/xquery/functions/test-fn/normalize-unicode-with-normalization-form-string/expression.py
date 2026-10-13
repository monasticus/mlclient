from mlclient.xquery import fn


def run():
    return fn.normalize_unicode("arg", normalization_form="NFC").compile()
