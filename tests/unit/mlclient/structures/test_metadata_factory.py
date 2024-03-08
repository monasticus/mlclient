from deepdiff import DeepDiff

from mlclient.structures import MetadataFactory
from tests.utils import resources as resources_utils


def test_from_json_file():
    metadata_file_path = resources_utils.get_test_resource_path(
        __file__,
        "metadata.json",
    )

    actual_metadata = MetadataFactory.from_file(metadata_file_path)

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

    actual_metadata = MetadataFactory.from_file(metadata_file_path)

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
