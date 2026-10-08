from mlclient.xquery import fn


def run():
    return fn.escape_html_uri("products/Mark Logic").compile()
