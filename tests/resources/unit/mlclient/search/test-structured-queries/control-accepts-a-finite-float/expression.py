from mlclient.search.options import opt


def run():
    return opt.options(opt.control("quality-weight", 0.5))
