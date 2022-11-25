import pytest

from mlclient.model import DocumentMetadata


@pytest.fixture
def metadata():
    collections = {"collection-1", "collection-2"}
    permissions = {"permission-1", "permission-2"}
    properties = {"prop-name-1": "prop-value-1", "prop-name-2": "prop-value-2"}
    quality = 1
    metadata_values = {"meta-name-1": "meta-value-1", "meta-name-2": "meta-value-2"}

    return DocumentMetadata(collections=collections,
                            permissions=permissions,
                            properties=properties,
                            quality=quality,
                            metadata_values=metadata_values)


def test_get_collections_when_exists():
    collections = {"collection-1", "collection-2"}
    metadata = DocumentMetadata(collections=collections)
    assert metadata.collections() == collections


def test_get_collections_when_empty():
    metadata = DocumentMetadata()
    assert metadata.collections() == set()


def test_get_permissions_when_exists():
    permissions = {"permission-1", "permission-2"}
    metadata = DocumentMetadata(permissions=permissions)
    assert metadata.permissions() == permissions


def test_get_permissions_when_empty():
    metadata = DocumentMetadata()
    assert metadata.permissions() == set()


def test_get_properties_when_exists():
    properties = {"prop-name-1": "prop-value-1", "prop-name-2": "prop-value-2"}
    metadata = DocumentMetadata(properties=properties)
    assert metadata.properties() == properties


def test_get_properties_when_empty():
    metadata = DocumentMetadata()
    assert metadata.properties() == {}


def test_get_quality_when_exists():
    quality = 1
    metadata = DocumentMetadata(quality=quality)
    assert metadata.quality() == quality


def test_get_quality_when_empty():
    metadata = DocumentMetadata()
    assert metadata.quality() is None


def test_get_metadata_values_when_exists():
    metadata_values = {"meta-name-1": "meta-value-1", "meta-name-2": "meta-value-2"}
    metadata = DocumentMetadata(metadata_values=metadata_values)
    assert metadata.metadata_values() == metadata_values


def test_get_metadata_values_when_empty():
    metadata = DocumentMetadata()
    assert metadata.metadata_values() == {}


def test_set_quality():
    metadata = DocumentMetadata()
    success = metadata.set_quality(1)
    assert success is True
    assert metadata.quality() == 1

    success = metadata.set_quality(2)
    assert success is True
    assert metadata.quality() == 2


def test_set_quality_when_not_int():
    metadata = DocumentMetadata()
    success = metadata.set_quality("1")
    assert success is False
    assert metadata.quality() is None


def test_add_collection():
    metadata = DocumentMetadata()
    success = metadata.add_collection("collection-1")
    assert success is True
    assert metadata.collections() == {"collection-1"}

    success = metadata.add_collection("collection-2")
    assert success is True
    assert metadata.collections() == {"collection-1", "collection-2"}


def test_add_collection_when_exists():
    metadata = DocumentMetadata(collections={"collection-1"})
    success = metadata.add_collection("collection-1")
    assert success is False
    assert metadata.collections() == {"collection-1"}


def test_add_none_collection():
    metadata = DocumentMetadata(collections={"collection-1"})
    success = metadata.add_collection(None)
    assert success is False
    assert metadata.collections() == {"collection-1"}


def test_add_blank_collection():
    metadata = DocumentMetadata(collections={"collection-1"})
    success = metadata.add_collection(" \n")
    assert success is False
    assert metadata.collections() == {"collection-1"}


def test_add_permission():
    metadata = DocumentMetadata()
    success = metadata.add_permission("permission-1")
    assert success is True
    assert metadata.permissions() == {"permission-1"}

    success = metadata.add_permission("permission-2")
    assert success is True
    assert metadata.permissions() == {"permission-1", "permission-2"}


def test_add_permission_when_exists():
    metadata = DocumentMetadata(permissions={"permission-1"})
    success = metadata.add_permission("permission-1")
    assert success is False
    assert metadata.permissions() == {"permission-1"}


def test_add_none_permission():
    metadata = DocumentMetadata(permissions={"permission-1"})
    success = metadata.add_permission(None)
    assert success is False
    assert metadata.permissions() == {"permission-1"}


def test_add_blank_permission():
    metadata = DocumentMetadata(permissions={"permission-1"})
    success = metadata.add_permission(" \n")
    assert success is False
    assert metadata.permissions() == {"permission-1"}


def test_put_property():
    metadata = DocumentMetadata()
    metadata.put_property("prop-name-1", "prop-value-1")
    assert metadata.properties() == {
        "prop-name-1": "prop-value-1"
    }

    metadata.put_property("prop-name-2", "prop-value-2")
    assert metadata.properties() == {
        "prop-name-1": "prop-value-1",
        "prop-name-2": "prop-value-2"
    }


def test_put_property_when_exists():
    metadata = DocumentMetadata(properties={"prop-name-1": "prop-value-1"})
    metadata.put_property("prop-name-1", "prop-value-2")
    assert metadata.properties() == {
        "prop-name-1": "prop-value-2"
    }


def test_put_none_property():
    metadata = DocumentMetadata(properties={"prop-name-1": "prop-value-1"})
    metadata.put_property("prop-name-1", None)
    assert metadata.properties() == {
        "prop-name-1": "prop-value-1"
    }


def test_put_metadata_value():
    metadata = DocumentMetadata()
    metadata.put_metadata_value("meta-name-1", "meta-value-1")
    assert metadata.metadata_values() == {
        "meta-name-1": "meta-value-1"
    }

    metadata.put_metadata_value("meta-name-2", "meta-value-2")
    assert metadata.metadata_values() == {
        "meta-name-1": "meta-value-1",
        "meta-name-2": "meta-value-2"
    }


def test_put_metadata_value_when_exists():
    metadata = DocumentMetadata(metadata_values={"meta-name-1": "meta-value-1"})
    metadata.put_metadata_value("meta-name-1", "meta-value-2")
    assert metadata.metadata_values() == {
        "meta-name-1": "meta-value-2"
    }


def test_put_none_metadata_value():
    metadata = DocumentMetadata(metadata_values={"meta-name-1": "meta-value-1"})
    metadata.put_metadata_value("meta-name-1", None)
    assert metadata.metadata_values() == {
        "meta-name-1": "meta-value-1"
    }


def test_remove_collection():
    metadata = DocumentMetadata(collections={"collection-1", "collection-2"})
    success = metadata.remove_collection("collection-1")
    assert success is True
    assert metadata.collections() == {"collection-2"}

    success = metadata.remove_collection("collection-2")
    assert success is True
    assert metadata.collections() == set()


def test_remove_collection_when_does_not_exist():
    metadata = DocumentMetadata(collections={"collection-1"})
    success = metadata.remove_collection("collection-2")
    assert success is False
    assert metadata.collections() == {"collection-1"}


def test_remove_permission():
    metadata = DocumentMetadata(permissions={"permission-1", "permission-2"})
    success = metadata.remove_permission("permission-1")
    assert success is True
    assert metadata.permissions() == {"permission-2"}

    success = metadata.remove_permission("permission-2")
    assert success is True
    assert metadata.permissions() == set()


def test_remove_permission_when_does_not_exist():
    metadata = DocumentMetadata(permissions={"permission-1"})
    success = metadata.remove_permission("permission-2")
    assert success is False
    assert metadata.permissions() == {"permission-1"}


def test_remove_property():
    metadata = DocumentMetadata(properties={"prop-name-1": "prop-value-1", "prop-name-2": "prop-value-2"})
    success = metadata.remove_property("prop-name-1")
    assert success is True
    assert metadata.properties() == {
        "prop-name-2": "prop-value-2"
    }

    success = metadata.remove_property("prop-name-2")
    assert success is True
    assert metadata.properties() == {}


def test_remove_property_when_does_not_exist():
    metadata = DocumentMetadata(properties={"prop-name-1": "prop-value-1"})
    success = metadata.remove_property("prop-name-2")
    assert success is False
    assert metadata.properties() == {
        "prop-name-1": "prop-value-1"
    }


def test_remove_metadata_value():
    metadata = DocumentMetadata(metadata_values={"meta-name-1": "meta-value-1", "meta-name-2": "meta-value-2"})
    success = metadata.remove_metadata_value("meta-name-1")
    assert success is True
    assert metadata.metadata_values() == {
        "meta-name-2": "meta-value-2"
    }

    success = metadata.remove_metadata_value("meta-name-2")
    assert success is True
    assert metadata.metadata_values() == {}


def test_remove_metadata_value_when_does_not_exist():
    metadata = DocumentMetadata(metadata_values={"meta-name-1": "meta-value-1"})
    success = metadata.remove_metadata_value("meta-name-2")
    assert success is False
    assert metadata.metadata_values() == {
        "meta-name-1": "meta-value-1"
    }


def test_properties_with_none_values():
    properties = {
        "prop-name-1": "prop-value-1",
        "prop-name-2": None,
        "prop-name-3": "prop-value-1",
        "prop-name-4": None
    }
    metadata = DocumentMetadata(properties=properties)
    assert metadata.properties() == {
        "prop-name-1": "prop-value-1",
        "prop-name-3": "prop-value-1"
    }


def test_metadata_values_with_none_values():
    metadata_values = {
        "meta-name-1": "meta-value-1",
        "meta-name-2": None,
        "meta-name-3": "meta-value-1",
        "meta-name-4": None
    }
    metadata = DocumentMetadata(metadata_values=metadata_values)
    assert metadata.metadata_values() == {
        "meta-name-1": "meta-value-1",
        "meta-name-3": "meta-value-1"
    }


def test_to_json(metadata):
    metadata_json = metadata.to_json()
    assert metadata_json == {
        "collections": {"collection-1", "collection-2"},
        "permissions": {"permission-1", "permission-2"},
        "properties": {
            "prop-name-1": "prop-value-1",
            "prop-name-2": "prop-value-2"
        },
        "quality": 1,
        "metadataValues": {
            "meta-name-1": "meta-value-1",
            "meta-name-2": "meta-value-2"
        }
    }


def test_to_json_string(metadata):
    metadata_json_string = metadata.to_json_string()
    assert "\n" not in metadata_json_string
    assert ('"collections": ["collection-1", "collection-2"]' in metadata_json_string or
            '"collections": ["collection-2", "collection-1"]' in metadata_json_string)
    assert ('"permissions": ["permission-1", "permission-2"]' in metadata_json_string or
            '"permissions": ["permission-2", "permission-1"]' in metadata_json_string)
    assert ('"properties": {"prop-name-1": "prop-value-1", "prop-name-2": "prop-value-2"}' in metadata_json_string or
            '"properties": {"prop-name-2": "prop-value-2", "prop-name-1": "prop-value-1"}' in metadata_json_string)
    assert '"quality": 1' in metadata_json_string
    assert ('"metadataValues": {"meta-name-1": "meta-value-1", "meta-name-2": "meta-value-2"}'
            in metadata_json_string or
            '"metadataValues": {"meta-name-2": "meta-value-2", "meta-name-1": "meta-value-1"}'
            in metadata_json_string)


def test_to_json_string_with_indent(metadata):
    metadata_json_string = metadata.to_json_string(indent=4)
    assert '{\n' in metadata_json_string
    assert '    "collections": [\n' in metadata_json_string
    assert '        "collection-1"\n' in metadata_json_string or '        "collection-1",\n' in metadata_json_string
    assert '        "collection-2"\n' in metadata_json_string or '        "collection-2",\n' in metadata_json_string
    assert '    ],\n' in metadata_json_string
    assert '    "permissions": [\n' in metadata_json_string
    assert '        "permission-1"\n' in metadata_json_string or '        "permission-1",\n' in metadata_json_string
    assert '        "permission-2"\n' in metadata_json_string or '        "permission-2",\n' in metadata_json_string
    assert '    ],\n' in metadata_json_string
    assert '"properties": {\n' in metadata_json_string
    assert ('        "prop-name-1": "prop-value-1"\n' in metadata_json_string or
            '        "prop-name-1": "prop-value-1",\n' in metadata_json_string)
    assert ('        "prop-name-2": "prop-value-2"\n' in metadata_json_string or
            '        "prop-name-2": "prop-value-2",\n' in metadata_json_string)
    assert '    },\n' in metadata_json_string or '    }\n' in metadata_json_string
    assert '    "quality": 1\n' in metadata_json_string or '    "quality": 1,\n' in metadata_json_string
    assert '    "metadataValues": {\n' in metadata_json_string
    assert ('        "meta-name-1": "meta-value-1"\n' in metadata_json_string or
            '        "meta-name-1": "meta-value-1",\n' in metadata_json_string)
    assert ('        "meta-name-2": "meta-value-2"\n' in metadata_json_string or
            '        "meta-name-2": "meta-value-2",\n' in metadata_json_string)
    assert '    }\n' in metadata_json_string or '    },\n' in metadata_json_string
    assert '}' in metadata_json_string


def test_to_xml(metadata):
    metadata_xml = metadata.to_xml()
    root = metadata_xml.getroot()
    assert root.tag == "rapi:metadata"
    assert root.attrib == {"xmlns:rapi": "http://marklogic.com/rest-api"}

    collections_element = root.find("rapi:collections")
    collection_elements = list(collections_element)
    assert collections_element is not None
    assert collections_element.attrib == {}
    assert len(collection_elements) == 2
    for collection_element in collection_elements:
        assert collection_element.tag == "rapi:collection"
        assert collection_element.attrib == {}
        assert len(list(collection_element)) == 0
        assert collection_element.text in ["collection-1", "collection-2"]

    permissions_element = root.find("rapi:permissions")
    permission_elements = list(permissions_element)
    assert permissions_element is not None
    assert permissions_element.attrib == {}
    assert len(permission_elements) == 2
    for permission_element in permission_elements:
        assert permission_element.tag == "rapi:permission"
        assert permission_element.attrib == {}
        assert len(list(permission_element)) == 0
        assert permission_element.text in ["permission-1", "permission-2"]

    properties_element = root.find("prop:properties")
    property_elements = list(properties_element)
    assert properties_element is not None
    assert properties_element.attrib == {"xmlns:prop": "http://marklogic.com/xdmp/property"}
    assert len(property_elements) == 2
    for property_element in property_elements:
        assert property_element.tag in ["prop-name-1", "prop-name-2"]
        assert property_element.attrib == {}
        assert len(list(property_element)) == 0
        assert property_element.text in ["prop-value-1", "prop-value-2"]

    quality_element = root.find("rapi:quality")
    assert quality_element is not None
    assert quality_element.attrib == {}
    assert len(list(quality_element)) == 0
    assert quality_element.text == "1"

    metadata_values_element = root.find("rapi:metadata-values")
    metadata_values_elements = list(metadata_values_element)
    assert metadata_values_element is not None
    assert metadata_values_element.attrib == {}
    assert len(metadata_values_elements) == 2
    for metadata_value_element in metadata_values_elements:
        assert metadata_value_element.tag == "rapi:metadata-value"
        assert metadata_value_element.attrib in [{"key": "meta-name-1"}, {"key": "meta-name-2"}]
        assert len(list(metadata_value_element)) == 0
        assert metadata_value_element.text in ["meta-value-1", "meta-value-2"]


def test_to_xml_string(metadata):
    metadata_xml_string = metadata.to_xml_string()
    assert "<?xml version='1.0' encoding='utf-8'?>\n" in metadata_xml_string
    assert '<rapi:metadata xmlns:rapi="http://marklogic.com/rest-api">' in metadata_xml_string
    assert '<rapi:collections>' in metadata_xml_string
    assert '<rapi:collection>collection-1</rapi:collection>' in metadata_xml_string
    assert '<rapi:collection>collection-2</rapi:collection>' in metadata_xml_string
    assert '</rapi:collections>' in metadata_xml_string
    assert '<rapi:permissions>' in metadata_xml_string
    assert '<rapi:permission>permission-1</rapi:permission>' in metadata_xml_string
    assert '<rapi:permission>permission-2</rapi:permission>' in metadata_xml_string
    assert '</rapi:permissions>' in metadata_xml_string
    assert '<prop:properties xmlns:prop="http://marklogic.com/xdmp/property">' in metadata_xml_string
    assert '<prop-name-1>prop-value-1</prop-name-1>' in metadata_xml_string
    assert '<prop-name-2>prop-value-2</prop-name-2>' in metadata_xml_string
    assert '</prop:properties>' in metadata_xml_string
    assert '<rapi:quality>1</rapi:quality>' in metadata_xml_string
    assert '<rapi:metadata-values>' in metadata_xml_string
    assert '<rapi:metadata-value key="meta-name-1">meta-value-1</rapi:metadata-value>' in metadata_xml_string
    assert '<rapi:metadata-value key="meta-name-2">meta-value-2</rapi:metadata-value>' in metadata_xml_string
    assert '</rapi:metadata-values>' in metadata_xml_string
    assert '</rapi:metadata>' in metadata_xml_string


def test_to_xml_string_with_indent(metadata):
    metadata_xml_string = metadata.to_xml_string(indent=4)
    assert '<?xml version="1.0" encoding="utf-8"?>\n' in metadata_xml_string
    assert '<rapi:metadata xmlns:rapi="http://marklogic.com/rest-api">\n' in metadata_xml_string
    assert '    <rapi:collections>\n' in metadata_xml_string
    assert '        <rapi:collection>collection-1</rapi:collection>\n' in metadata_xml_string
    assert '        <rapi:collection>collection-2</rapi:collection>\n' in metadata_xml_string
    assert '    </rapi:collections>\n' in metadata_xml_string
    assert '    <rapi:permissions>\n' in metadata_xml_string
    assert '        <rapi:permission>permission-1</rapi:permission>\n' in metadata_xml_string
    assert '        <rapi:permission>permission-2</rapi:permission>\n' in metadata_xml_string
    assert '    </rapi:permissions>\n' in metadata_xml_string
    assert '    <prop:properties xmlns:prop="http://marklogic.com/xdmp/property">\n' in metadata_xml_string
    assert '        <prop-name-1>prop-value-1</prop-name-1>\n' in metadata_xml_string
    assert '        <prop-name-2>prop-value-2</prop-name-2>\n' in metadata_xml_string
    assert '    </prop:properties>\n' in metadata_xml_string
    assert '    <rapi:quality>1</rapi:quality>\n' in metadata_xml_string
    assert '    <rapi:metadata-values>\n' in metadata_xml_string
    assert '        <rapi:metadata-value key="meta-name-1">meta-value-1</rapi:metadata-value>\n' in metadata_xml_string
    assert '        <rapi:metadata-value key="meta-name-2">meta-value-2</rapi:metadata-value>\n' in metadata_xml_string
    assert '    </rapi:metadata-values>\n' in metadata_xml_string
    assert '</rapi:metadata>\n' in metadata_xml_string
