import pytest

from mlclient import exceptions
from mlclient.calls import DatabaseDeleteCall


@pytest.fixture()
def default_database_delete_call():
    """Returns an DatabaseDeleteCall instance"""
    return DatabaseDeleteCall(database="Documents")


def test_validation_forest_delete_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        DatabaseDeleteCall(database="Documents", forest_delete="X")

    expected_msg = "The supported forest_delete options are: configuration, data"
    assert err.value.args[0] == expected_msg


def test_endpoint():
    expected__id_endpoint = "/manage/v2/databases/1"
    expected__name_endpoint = "/manage/v2/databases/Documents"
    assert DatabaseDeleteCall(
        database="1").endpoint() == expected__id_endpoint
    assert DatabaseDeleteCall(
        database="Documents").endpoint() == expected__name_endpoint


def test_method(default_database_delete_call):
    assert default_database_delete_call.method == "DELETE"


def test_parameters(default_database_delete_call):
    assert default_database_delete_call.params == {}


def test_parameters_for_forest_delete():
    call = DatabaseDeleteCall(database="Documents", forest_delete="configuration")
    assert call.params == {
        "forest-delete": "configuration",
    }


def test_headers(default_database_delete_call):
    assert default_database_delete_call.headers == {}


def test_body(default_database_delete_call):
    assert default_database_delete_call.body is None


def test_fully_parametrized_call():
    call = DatabaseDeleteCall(database="Documents", forest_delete="data")
    assert call.method == "DELETE"
    assert call.headers == {}
    assert call.params == {
        "forest-delete": "data",
    }
    assert call.body is None
