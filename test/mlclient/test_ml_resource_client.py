import pytest

from mlclient import MLResourceClient
from mlclient.calls import EvalCall


@pytest.fixture
def xquery():
    return """xquery version '1.0-ml';
    
    declare variable $element as element() external;
    
    <new-parent>{$element/child::element()}</new-parent>
    """


@pytest.mark.ml_access
def test_call(xquery):
    eval_call = EvalCall(xquery=xquery, variables={"element": "<parent><child/></parent>"})
    with MLResourceClient(auth_method="digest") as client:
        resp = client.call(eval_call)

    assert resp.status_code == 200
    assert "<new-parent><child/></new-parent>" in resp.text


@pytest.mark.ml_access
def test_eval(xquery):
    with MLResourceClient(auth_method="digest") as client:
        resp = client.eval(xquery=xquery, variables={"element": "<parent><child/></parent>"})

    assert resp.status_code == 200
    assert "<new-parent><child/></new-parent>" in resp.text


@pytest.mark.ml_access
def test_get_logs():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.get_logs(filename="ErrorLog.txt", data_format="json")

    assert resp.status_code == 200
    assert "logfile" in resp.json()


@pytest.mark.ml_access
def test_get_databases():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.get_databases(data_format="json")

    assert resp.status_code == 200
    assert "/manage/v2/databases?view=default" == resp.json()["database-default-list"]["meta"]["uri"]


@pytest.mark.ml_access
def test_post_databases():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.post_databases(body='<database-properties xmlns="http://marklogic.com/manage" />')

    assert resp.status_code == 400
    assert "Payload has errors in structure, content-type or values. Database name missing." in resp.text


@pytest.mark.ml_access
def test_get_database():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.get_database(database_name="Documents", data_format="json")

    assert resp.status_code == 200
    assert "/manage/v2/databases/Documents?view=default" == resp.json()["database-default"]["meta"]["uri"]


@pytest.mark.ml_access
def test_post_databases():
    with MLResourceClient(auth_method="digest") as client:
        resp = client.post_database(database_name="Documents", body={"operation": "clear-database"})

    assert resp.status_code == 200
    assert not resp.text
