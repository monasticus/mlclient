import pytest

from mlclient import exceptions
from mlclient.calls import DocumentsPostCall
from mlclient.model.calls import DocumentsBodyPart


@pytest.fixture()
def default_body_part():
    body_part = {
        "content-disposition": {
            "body_part_type": "attachment",
            "filename": "/path/to/file.json",
        },
        "content": '{"root": "data"}',
    }
    return DocumentsBodyPart(**body_part)


@pytest.fixture()
def default_databases_post_call(default_body_part):
    """Returns an DocumentsPostCall instance"""
    return DocumentsPostCall(body_parts=[default_body_part])


def test_validation_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        DocumentsPostCall(body_parts=None)

    expected_msg = ("No request body provided for "
                    "POST /v1/documents!")
    assert err.value.args[0] == expected_msg


def test_validation_empty_body_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        DocumentsPostCall(body_parts=[])

    expected_msg = ("No request body provided for "
                    "POST /v1/documents!")
    assert err.value.args[0] == expected_msg


def test_endpoint(default_databases_post_call):
    assert default_databases_post_call.endpoint == "/v1/documents"


def test_method(default_databases_post_call):
    assert default_databases_post_call.method == "POST"


def test_parameters(default_databases_post_call):
    assert default_databases_post_call.params == {}


def test_headers(default_databases_post_call):
    headers = default_databases_post_call.headers
    assert len(headers) == 2
    assert headers["Accept"] == "application/json"
    assert headers["Content-Type"].startswith("multipart/mixed; boundary=")


def test_body(default_body_part):
    call = DocumentsPostCall(body_parts=[default_body_part])
    boundary = call.headers["Content-Type"].replace("multipart/mixed; boundary=", "")
    expected_body = f"--{boundary}\r\n"
    expected_body += "Content-Disposition: attachment; filename=/path/to/file.json\r\n"
    expected_body += "Content-Type: application/json\r\n"
    expected_body += "\r\n"
    expected_body += '{"root": "data"}\r\n'
    expected_body += f"--{boundary}--\r\n"
    assert call.body == expected_body.encode("utf-8")


def test_body_with_dict_content():
    body_part = {
        "content-disposition": {
            "body_part_type": "attachment",
            "filename": "/path/to/file.json",
        },
        "content": {"root": "data"},
    }
    call = DocumentsPostCall(body_parts=[DocumentsBodyPart(**body_part)])
    boundary = call.headers["Content-Type"].replace("multipart/mixed; boundary=", "")
    expected_body = f"--{boundary}\r\n"
    expected_body += "Content-Disposition: attachment; filename=/path/to/file.json\r\n"
    expected_body += "Content-Type: application/json\r\n"
    expected_body += "\r\n"
    expected_body += '{"root": "data"}\r\n'
    expected_body += f"--{boundary}--\r\n"
    assert call.body == expected_body.encode("utf-8")


def test_fully_parametrized_call_for_multiple_uris_metadata(default_body_part):
    call = DocumentsPostCall(
        body_parts=[default_body_part],
        database="Documents",
        transform="custom-transformation",
        transform_params={"custom-param-1": "custom-value-1",
                          "custom-param-2": "custom-value-2"},
        txid="transaction",
        temporal_collection="Entity-collection",
        system_time="1900-01-01T01:01:01.001Z")
    assert call.method == "POST"
    assert len(call.headers) == 2
    assert call.headers["Accept"] == "application/json"
    assert call.headers["Content-Type"].startswith("multipart/mixed; boundary=")
    assert call.params == {
        "database": "Documents",
        "transform": "custom-transformation",
        "trans:custom-param-1": "custom-value-1",
        "trans:custom-param-2": "custom-value-2",
        "txid": "transaction",
        "temporal-collection": "Entity-collection",
        "system-time": "1900-01-01T01:01:01.001Z",
    }
    boundary = call.headers["Content-Type"].replace("multipart/mixed; boundary=", "")
    expected_body = f"--{boundary}\r\n"
    expected_body += "Content-Disposition: attachment; filename=/path/to/file.json\r\n"
    expected_body += "Content-Type: application/json\r\n"
    expected_body += "\r\n"
    expected_body += '{"root": "data"}\r\n'
    expected_body += f"--{boundary}--\r\n"
    assert call.body == expected_body.encode("utf-8")
