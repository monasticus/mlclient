from mlclient.xquery import DatabaseRoot


def test_database_root_compiles_fixed_path():
    code, variables = DatabaseRoot().compile()

    assert code == 'xquery version "1.0-ml";\n/'
    assert variables == {}
