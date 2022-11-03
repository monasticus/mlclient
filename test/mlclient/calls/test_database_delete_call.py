import pytest

from mlclient import exceptions
from mlclient.calls import DatabaseDeleteCall


@pytest.fixture
def default_database_delete_call():
    """Returns an DatabaseDeleteCall instance"""
    return DatabaseDeleteCall(database_name="Documents")


def test_validation_no_database_id_nor_database_name():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabaseDeleteCall()

    assert err.value.args[0] == "You must include either the database_id or the database_name parameter!"


def test_validation_forest_delete_param():
    with pytest.raises(exceptions.WrongParameters) as err:
        DatabaseDeleteCall(database_name="Documents", forest_delete="X")

    assert err.value.args[0] == "The supported forest_delete options are: configuration, data"


def test_endpoint(default_database_delete_call):
    assert DatabaseDeleteCall(database_id="1").endpoint() == "/manage/v2/databases/1"
    assert DatabaseDeleteCall(database_name="Documents").endpoint() == "/manage/v2/databases/Documents"
    assert DatabaseDeleteCall(database_id="1",
                              database_name="Documents").endpoint() == "/manage/v2/databases/1"


def test_method(default_database_delete_call):
    assert default_database_delete_call.method() == "DELETE"


def test_headers():
    call = DatabaseDeleteCall(database_name="Documents")
    assert {} == call.headers()


def test_parameters_for_no_forest_delete():
    call = DatabaseDeleteCall(database_name="Documents")
    assert {} == call.params()


def test_parameters_for_some_forest_delete():
    call = DatabaseDeleteCall(database_name="Documents", forest_delete="configuration")
    assert {
        "forest-delete": "configuration"
    } == call.params()


def test_body():
    call = DatabaseDeleteCall(database_name="Documents")
    assert not call.body()


def test_fully_parametrized_call():
    call = DatabaseDeleteCall(database_name="Documents", forest_delete="data")
    assert call.method() == "DELETE"
    assert {} == call.headers()
    assert {
        "forest-delete": "data"
    } == call.params()
    assert not call.body()
