import pytest
from deepdiff import DeepDiff

from mlclient.exceptions import InvalidMetadataError
from mlclient.models import Metadata
from tests.utils import resources as resources_utils


def test_from_json_file():
    metadata_file_path = resources_utils.get_test_resource_path(
        __file__,
        "metadata.json",
    )

    actual_metadata = Metadata.from_file(metadata_file_path)

    expected_metadata_json = {
        "collections": ["collection-1"],
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

    actual_metadata = Metadata.from_file(metadata_file_path)

    expected_metadata_json = {
        "collections": ["collection-1"],
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


def test_from_xml_file_with_wrong_root_namespace():
    metadata_file_path = resources_utils.get_test_resource_path(
        __file__,
        "metadata-wrong-root-namespace.xml",
    )

    with pytest.raises(InvalidMetadataError, match="Unexpected root element"):
        Metadata.from_file(metadata_file_path)


def test_from_xml_file_with_wrong_root_local_name():
    metadata_file_path = resources_utils.get_test_resource_path(
        __file__,
        "metadata-wrong-root-local-name.xml",
    )

    with pytest.raises(InvalidMetadataError, match="Unexpected root element"):
        Metadata.from_file(metadata_file_path)


def test_from_xml_file_with_wrong_child_namespace():
    metadata_file_path = resources_utils.get_test_resource_path(
        __file__,
        "metadata-wrong-child-namespace.xml",
    )

    with pytest.raises(InvalidMetadataError, match="Unexpected element"):
        Metadata.from_file(metadata_file_path)


def test_from_xml_file_with_wrong_child_local_name():
    metadata_file_path = resources_utils.get_test_resource_path(
        __file__,
        "metadata-wrong-child-local-name.xml",
    )

    with pytest.raises(InvalidMetadataError, match="Unexpected element"):
        Metadata.from_file(metadata_file_path)


def test_from_xml_file_with_no_namespace():
    metadata_file_path = resources_utils.get_test_resource_path(
        __file__,
        "metadata-no-namespace.xml",
    )

    with pytest.raises(InvalidMetadataError, match="Unexpected root element"):
        Metadata.from_file(metadata_file_path)
