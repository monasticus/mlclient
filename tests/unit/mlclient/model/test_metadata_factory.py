from deepdiff import DeepDiff

from mlclient.model import MetadataFactory
from tests.utils import resources as resources_utils


def test_from_json_file():
    metadata_file_path = resources_utils.get_test_resource_path(
        __file__,
        "metadata.json",
    )

    actual_metadata = MetadataFactory.from_file(metadata_file_path)

    expected_metadata_json = {
        "collections": ["collection-2", "collection-1"],
        "permissions": [
            {"role-name": "role-1", "capabilities": ["read"]},
            {"role-name": "role-2", "capabilities": ["update", "read"]},
        ],
        "properties": {"prop-name-1": "prop-value-1", "prop-name-2": "prop-value-2"},
        "quality": 1,
        "metadataValues": {
            "meta-name-1": "meta-1",
            "meta-name-2": "meta-2",
        },
    }
    diff = DeepDiff(
        actual_metadata.to_json(),
        expected_metadata_json,
        ignore_order=True,
    )
    assert not diff


def test_from_xml_file():
    metadata_file_path = resources_utils.get_test_resource_path(
        __file__,
        "metadata.xml",
    )

    actual_metadata = MetadataFactory.from_file(metadata_file_path)

    expected_metadata_json = {
        "collections": ["collection-2", "collection-1"],
        "permissions": [
            {"role-name": "role-1", "capabilities": ["read"]},
            {"role-name": "role-2", "capabilities": ["update", "read"]},
        ],
        "properties": {"prop-name-1": "prop-value-1", "prop-name-2": "prop-value-2"},
        "quality": 1,
        "metadataValues": {
            "meta-name-1": "meta-1",
            "meta-name-2": "meta-2",
        },
    }
    diff = DeepDiff(
        actual_metadata.to_json(),
        expected_metadata_json,
        ignore_order=True,
    )
    assert not diff


def test_from_json_file_raw():
    metadata_file_path = resources_utils.get_test_resource_path(
        __file__,
        "metadata.json",
    )

    actual_metadata = MetadataFactory.from_file(metadata_file_path, raw=True)

    expected_metadata = (
        b"{\n"
        b'  "collections": [\n'
        b'    "collection-1",\n'
        b'    "collection-2"\n'
        b"  ],\n"
        b'  "permissions": [\n'
        b"    {\n"
        b'      "role-name": "role-1",\n'
        b'      "capabilities": [\n'
        b'        "read"\n'
        b"      ]\n"
        b"    },\n"
        b"    {\n"
        b'      "role-name": "role-2",\n'
        b'      "capabilities": [\n'
        b'        "update",\n'
        b'        "read"\n'
        b"      ]\n"
        b"    }\n"
        b"  ],\n"
        b'  "properties": {\n'
        b'    "prop-name-1": "prop-value-1",\n'
        b'    "prop-name-2": "prop-value-2"\n'
        b"  },\n"
        b'  "quality": 1,\n'
        b'  "metadataValues": {\n'
        b'    "meta-name-1": "meta-1",\n'
        b'    "meta-name-2": "meta-2"\n'
        b"  }\n"
        b"}"
    )

    assert actual_metadata == expected_metadata


def test_from_xml_file_raw():
    metadata_file_path = resources_utils.get_test_resource_path(
        __file__,
        "metadata.xml",
    )

    actual_metadata = MetadataFactory.from_file(metadata_file_path, raw=True)

    expected_metadata = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<rapi:metadata xmlns:rapi="http://marklogic.com/rest-api">\n'
        b"    <rapi:collections>\n"
        b"        <rapi:collection>collection-1</rapi:collection>\n"
        b"        <rapi:collection>collection-2</rapi:collection>\n"
        b"    </rapi:collections>\n"
        b"    <rapi:permissions>\n"
        b"        <rapi:permission>\n"
        b"            <rapi:role-name>role-1</rapi:role-name>\n"
        b"            <rapi:capability>read</rapi:capability>\n"
        b"        </rapi:permission>\n"
        b"        <rapi:permission>\n"
        b"            <rapi:role-name>role-2</rapi:role-name>\n"
        b"            <rapi:capability>update</rapi:capability>\n"
        b"        </rapi:permission>\n"
        b"        <rapi:permission>\n"
        b"            <rapi:role-name>role-2</rapi:role-name>\n"
        b"            <rapi:capability>read</rapi:capability>\n"
        b"        </rapi:permission>\n"
        b"    </rapi:permissions>\n"
        b'    <prop:properties xmlns:prop="http://marklogic.com/xdmp/property">\n'
        b"        <prop-name-1>prop-value-1</prop-name-1>\n"
        b"        <prop-name-2>prop-value-2</prop-name-2>\n"
        b"    </prop:properties>\n"
        b"    <rapi:quality>1</rapi:quality>\n"
        b"    <rapi:metadata-values>\n"
        b'        <rapi:metadata-value key="meta-name-1">meta-1</rapi:metadata-value>\n'
        b'        <rapi:metadata-value key="meta-name-2">meta-2</rapi:metadata-value>\n'
        b"    </rapi:metadata-values>\n"
        b"</rapi:metadata>"
    )

    assert actual_metadata == expected_metadata
