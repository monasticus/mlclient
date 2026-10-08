from mlclient.xquery import fn


def run():
    return fn.system_property("xsl:version").compile()
