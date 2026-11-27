import pytest

from mlclient import exceptions
from mlclient.calls import DocumentsGetCall


@pytest.fixture
def default_documents_get_call():
    """Returns an DocumentsGetCall instance"""
    return DocumentsGetCall(uri="/a.xml")


def test_validation_category_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        DocumentsGetCall(uri="/a.xml", category="X")

    expected_msg = (
        "The supported categories are: "
        "content, metadata, metadata-values, collections, "
        "permissions, properties, quality"
    )
    assert err.value.args[0] == expected_msg


def test_validation_multiple_categories_param():
    with pytest.raises(exceptions.WrongParametersError) as err:
        DocumentsGetCall(uri="/a.xml", category=["collections", "X"])

    expected_msg = (
        "The supported categories are: "
        "content, metadata, metadata-values, collections, "
        "permissions, properties, quality"
    )
    assert err.value.args[0] == expected_msg


@pytest.mark.parametrize("data_format", ["html", "unknown"])
@pytest.mark.parametrize(
    "category",
    [None, "content", ["content"], "metadata", ["content", "collections"]],
)
def test_validation_format_param(category, data_format):
    with pytest.raises(exceptions.WrongParametersError) as err:
        DocumentsGetCall(uri="/a.xml", category=category, data_format=data_format)

    assert str(err.value) == "The supported formats are: binary, json, text, xml"


@pytest.mark.parametrize("data_format", ["binary", "text"])
@pytest.mark.parametrize("category", ["metadata", ["content", "collections"]])
def test_validation_metadata_format_param(category, data_format):
    with pytest.raises(exceptions.WrongParametersError) as err:
        DocumentsGetCall(uri="/a.xml", category=category, data_format=data_format)

    assert str(err.value) == "The supported metadata formats are: json, xml"


@pytest.mark.parametrize("data_format", ["binary", "text"])
@pytest.mark.parametrize("category", [None, "", [], "content", ["content"]])
def test_content_only_accepts_text_and_binary_without_conversion(category, data_format):
    call = DocumentsGetCall(uri="/a.xml", category=category, data_format=data_format)

    assert call.params["format"] == data_format
    assert call.headers == {}


def test_validation_timestamp_with_txid():
    with pytest.raises(exceptions.WrongParametersError) as err:
        DocumentsGetCall(uri="/a.xml", timestamp="16692287403272560", txid="tx")

    expected_msg = "timestamp cannot be combined with txid"
    assert err.value.args[0] == expected_msg


@pytest.mark.parametrize("data_format", ["json", "xml"])
@pytest.mark.parametrize(
    "category",
    [None, "content", ["content"], "metadata", ["content", "collections"]],
)
def test_validation_accepts_metadata_format_for_any_category(category, data_format):
    call = DocumentsGetCall(uri="/a.xml", category=category, data_format=data_format)

    assert call.params["format"] == data_format


def test_endpoint(default_documents_get_call):
    assert default_documents_get_call.endpoint == "/v1/documents"


def test_method(default_documents_get_call):
    assert default_documents_get_call.method == "GET"


def test_parameters_single_uri():
    assert DocumentsGetCall(uri="/a.xml").params == {
        "uri": "/a.xml",
    }


def test_parameters_multiple_uris():
    assert DocumentsGetCall(uri=["/a.xml", "/b.xml"]).params == {
        "uri": ["/a.xml", "/b.xml"],
    }


def test_parameters_single_category():
    assert DocumentsGetCall(
        uri="/a.xml",
        category="collections",
    ).params == {
        "uri": "/a.xml",
        "category": "collections",
    }


def test_parameters_multiple_categories():
    assert DocumentsGetCall(
        uri="/a.xml",
        category=["collections", "permissions"],
    ).params == {
        "uri": "/a.xml",
        "category": ["collections", "permissions"],
    }


def test_headers_for_single_uri_and_no_format():
    assert DocumentsGetCall(uri="/a.xml").headers == {}


def test_headers_for_single_uri_and_none_format():
    assert DocumentsGetCall(uri="/a.xml", data_format=None).headers == {}


def test_headers_for_single_uri_no_category_and_format():
    assert DocumentsGetCall(uri="/a.xml", data_format="json").headers == {}


def test_headers_for_single_uri_content_category_and_format():
    assert (
        DocumentsGetCall(uri="/a.xml", category="content", data_format="json").headers
        == {}
    )


def test_headers_for_single_uri_content_category_list_and_format():
    assert (
        DocumentsGetCall(
            uri="/a.xml",
            category=["content"],
            data_format="json",
        ).headers
        == {}
    )


def test_headers_for_single_uri_single_metadata_category_list_and_format():
    assert DocumentsGetCall(
        uri="/a.xml",
        category=["collections"],
        data_format="xml",
    ).headers == {
        "Accept": "application/xml",
    }


def test_headers_for_single_uri_metadata_category_and_json_format():
    assert DocumentsGetCall(
        uri="/a.xml",
        category="collections",
        data_format="json",
    ).headers == {
        "Accept": "application/json",
    }


def test_headers_for_single_uri_metadata_category_and_xml_format():
    assert DocumentsGetCall(
        uri="/a.xml",
        category="collections",
        data_format="xml",
    ).headers == {
        "Accept": "application/xml",
    }


def test_headers_for_multiple_uris_and_no_format():
    assert DocumentsGetCall(uri=["/a.xml", "/b.xml"]).headers == {
        "Accept": "multipart/mixed",
    }


def test_headers_for_multiple_uris_and_none_format():
    assert DocumentsGetCall(uri=["/a.xml", "/b.xml"], data_format=None).headers == {
        "Accept": "multipart/mixed",
    }


def test_headers_for_multiple_uris_no_category_and_format():
    assert DocumentsGetCall(uri=["/a.xml", "/b.xml"], data_format="json").headers == {
        "Accept": "multipart/mixed",
    }


def test_headers_for_multiple_uris_content_category_and_format():
    assert DocumentsGetCall(
        uri=["/a.xml", "/b.xml"],
        category="content",
        data_format="json",
    ).headers == {
        "Accept": "multipart/mixed",
    }


def test_headers_for_multiple_uris_metadata_category_and_json_format():
    assert DocumentsGetCall(
        uri=["/a.xml", "/b.xml"],
        category="collections",
        data_format="json",
    ).headers == {
        "Accept": "multipart/mixed",
    }


def test_headers_for_multiple_uris_metadata_category_and_xml_format():
    assert DocumentsGetCall(
        uri=["/a.xml", "/b.xml"],
        category="collections",
        data_format="xml",
    ).headers == {
        "Accept": "multipart/mixed",
    }


def test_body(default_documents_get_call):
    assert default_documents_get_call.body is None


def test_fully_parametrized_call_for_single_uri_content():
    call = DocumentsGetCall(
        uri="/a.xml",
        database="Documents",
        timestamp="16692287403272560",
        transform="custom-transformation",
        params={
            "trans:custom-param-1": "custom-value-1",
            "trans:custom-param-2": "custom-value-2",
        },
    )
    assert call.method == "GET"
    assert call.headers == {}
    assert call.params == {
        "uri": "/a.xml",
        "database": "Documents",
        "timestamp": "16692287403272560",
        "transform": "custom-transformation",
        "trans:custom-param-1": "custom-value-1",
        "trans:custom-param-2": "custom-value-2",
    }
    assert call.body is None


def test_fully_parametrized_call_for_single_uri_metadata():
    call = DocumentsGetCall(
        uri="/a.xml",
        database="Documents",
        category="properties",
        data_format="xml",
        transform="custom-transformation",
        params={
            "trans:custom-param-1": "custom-value-1",
            "trans:custom-param-2": "custom-value-2",
        },
        txid="transaction",
    )
    assert call.method == "GET"
    assert call.headers == {
        "Accept": "application/xml",
    }
    assert call.params == {
        "uri": "/a.xml",
        "database": "Documents",
        "category": "properties",
        "format": "xml",
        "transform": "custom-transformation",
        "trans:custom-param-1": "custom-value-1",
        "trans:custom-param-2": "custom-value-2",
        "txid": "transaction",
    }
    assert call.body is None


def test_fully_parametrized_call_for_multiple_uris_metadata():
    call = DocumentsGetCall(
        uri=["/a.xml", "/b.xml"],
        database="Documents",
        category="collections",
        data_format="json",
        timestamp="16692287403272560",
        transform="custom-transformation",
        params={
            "trans:custom-param-1": "custom-value-1",
            "trans:custom-param-2": "custom-value-2",
        },
    )
    assert call.method == "GET"
    assert call.headers == {
        "Accept": "multipart/mixed",
    }
    assert call.params == {
        "uri": ["/a.xml", "/b.xml"],
        "database": "Documents",
        "category": "collections",
        "format": "json",
        "timestamp": "16692287403272560",
        "transform": "custom-transformation",
        "trans:custom-param-1": "custom-value-1",
        "trans:custom-param-2": "custom-value-2",
    }
    assert call.body is None


def test_fully_parametrized_call_for_single_uri_and_multiple_categories():
    call = DocumentsGetCall(
        uri="/a.xml",
        database="Documents",
        category=["collections", "properties"],
        data_format="xml",
        transform="custom-transformation",
        params={
            "trans:custom-param-1": "custom-value-1",
            "trans:custom-param-2": "custom-value-2",
        },
        txid="transaction",
    )
    assert call.method == "GET"
    assert call.headers == {
        "Accept": "multipart/mixed",
    }
    assert call.params == {
        "uri": "/a.xml",
        "database": "Documents",
        "category": ["collections", "properties"],
        "format": "xml",
        "transform": "custom-transformation",
        "trans:custom-param-1": "custom-value-1",
        "trans:custom-param-2": "custom-value-2",
        "txid": "transaction",
    }
    assert call.body is None


def test_params_preserve_false_zero_and_empty_values():
    call = DocumentsGetCall(
        uri="/a.json",
        transform="tag",
        params={
            "trans:flag": False,
            "trans:limit": 0,
            "trans:label": "",
            "trans:omit": None,
        },
    )

    assert call.params == {
        "uri": "/a.json",
        "transform": "tag",
        "trans:flag": False,
        "trans:limit": 0,
        "trans:label": "",
    }


@pytest.mark.parametrize("transform", [None, ""])
def test_prefixed_params_require_transform(transform):
    with pytest.raises(exceptions.WrongParametersError) as error:
        DocumentsGetCall(
            "/example.xml",
            transform=transform,
            params={"trans:tag": "x"},
        )
    assert str(error.value) == "trans: parameters require transform"


def test_additional_params_are_validated_with_named_arguments():
    with pytest.raises(exceptions.WrongParametersError) as error:
        DocumentsGetCall("/a.xml", timestamp="1", params={"txid": "tx"})
    assert str(error.value) == "timestamp cannot be combined with txid"


def test_named_arguments_take_precedence_over_additional_params():
    call = DocumentsGetCall("/a.xml", data_format="json", params={"format": "text"})
    assert call.params["format"] == "json"


def test_omitted_transform_params_do_not_require_transform():
    call = DocumentsGetCall("/a.xml", params={"trans:omit": None})
    assert call.params == {"uri": "/a.xml"}
