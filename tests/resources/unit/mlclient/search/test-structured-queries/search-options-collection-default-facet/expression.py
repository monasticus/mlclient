from mlclient.search.options import opt


def run():
    return opt.options(opt.collection_constraint("type"))
