import copy

import pytest
from typing import List

from mlclient.model import Metadata, Permission


def __assert_permissions_are_equal(
        these_permissions: List[Permission],
        those_permissions: List[Permission],
):
    assert len(these_permissions) == len(those_permissions)
    for this_permission in these_permissions:
        this_role = this_permission.role_name()
        that_permission = next((permission
                                for permission in those_permissions
                                if permission.role_name() == this_role), None)
        assert that_permission is not None

        this_capabilities = this_permission.capabilities()
        that_capabilities = that_permission.capabilities()
        assert this_capabilities.difference(that_capabilities) == set()


@pytest.fixture()
def metadata():
    collections = ["collection-1", "collection-2"]
    permissions = [
        Permission("role-1", {Permission.READ}),
        Permission("role-2", {Permission.READ, Permission.UPDATE}),
    ]
    properties = {"prop-name-1": "prop-value-1", "prop-name-2": "prop-value-2"}
    quality = 1
    metadata_values = {"meta-name-1": "meta-value-1", "meta-name-2": "meta-value-2"}

    return Metadata(collections=collections,
                    permissions=permissions,
                    properties=properties,
                    quality=quality,
                    metadata_values=metadata_values)


def test_equal():
    collections = ["collection-1", "collection-2"]
    permissions = [Permission("role-1", {Permission.READ})]
    properties = {"prop-name-1": "prop-value-1", "prop-name-2": "prop-value-2"}
    metadata_values = {"meta-name-1": "meta-value-1", "meta-name-2": "meta-value-2"}
    metadata_1 = Metadata(collections=collections,
                          permissions=permissions,
                          properties=properties,
                          quality=1,
                          metadata_values=metadata_values)
    metadata_2 = Metadata(collections=collections,
                          permissions=permissions,
                          properties=properties,
                          quality=1,
                          metadata_values=metadata_values)
    assert metadata_1 == metadata_2
    assert metadata_1.__hash__() == metadata_2.__hash__()


def test_not_equal_when_collections_differ():
    collections_1 = ["collection-1", "collection-2"]
    collections_2 = ["collection-1", "collection-3"]
    permissions = [Permission("role-1", {Permission.READ})]
    properties = {"prop-name-1": "prop-value-1", "prop-name-2": "prop-value-2"}
    metadata_values = {"meta-name-1": "meta-value-1", "meta-name-2": "meta-value-2"}
    metadata_1 = Metadata(collections=collections_1,
                          permissions=permissions,
                          properties=properties,
                          quality=1,
                          metadata_values=metadata_values)
    metadata_2 = Metadata(collections=collections_2,
                          permissions=permissions,
                          properties=properties,
                          quality=1,
                          metadata_values=metadata_values)
    assert metadata_1 != metadata_2
    assert metadata_1.__hash__() != metadata_2.__hash__()


def test_not_equal_when_permissions_differ():
    collections = ["collection-1", "collection-2"]
    permissions_1 = [Permission("role-1", {Permission.READ})]
    permissions_2 = [Permission("role-1", {Permission.UPDATE})]
    properties = {"prop-name-1": "prop-value-1", "prop-name-2": "prop-value-2"}
    metadata_values = {"meta-name-1": "meta-value-1", "meta-name-2": "meta-value-2"}
    metadata_1 = Metadata(collections=collections,
                          permissions=permissions_1,
                          properties=properties,
                          quality=1,
                          metadata_values=metadata_values)
    metadata_2 = Metadata(collections=collections,
                          permissions=permissions_2,
                          properties=properties,
                          quality=1,
                          metadata_values=metadata_values)
    assert metadata_1 != metadata_2
    assert metadata_1.__hash__() != metadata_2.__hash__()


def test_not_equal_when_properties_differ():
    collections = ["collection-1", "collection-2"]
    permissions = [Permission("role-1", {Permission.READ})]
    properties_1 = {"prop-name-1": "prop-value-1", "prop-name-2": "prop-value-2"}
    properties_2 = {"prop-name-1": "prop-value-1", "prop-name-2": "prop-value-3"}
    metadata_values = {"meta-name-1": "meta-value-1", "meta-name-2": "meta-value-2"}
    metadata_1 = Metadata(collections=collections,
                          permissions=permissions,
                          properties=properties_1,
                          quality=1,
                          metadata_values=metadata_values)
    metadata_2 = Metadata(collections=collections,
                          permissions=permissions,
                          properties=properties_2,
                          quality=1,
                          metadata_values=metadata_values)
    assert metadata_1 != metadata_2
    assert metadata_1.__hash__() != metadata_2.__hash__()


def test_not_equal_when_qualities_differ():
    collections = ["collection-1", "collection-2"]
    permissions = [Permission("role-1", {Permission.READ})]
    properties = {"prop-name-1": "prop-value-1", "prop-name-2": "prop-value-2"}
    metadata_values = {"meta-name-1": "meta-value-1", "meta-name-2": "meta-value-2"}
    metadata_1 = Metadata(collections=collections,
                          permissions=permissions,
                          properties=properties,
                          quality=1,
                          metadata_values=metadata_values)
    metadata_2 = Metadata(collections=collections,
                          permissions=permissions,
                          properties=properties,
                          quality=2,
                          metadata_values=metadata_values)
    assert metadata_1 != metadata_2
    assert metadata_1.__hash__() != metadata_2.__hash__()


def test_not_equal_when_metadata_values_differ():
    collections = ["collection-1", "collection-2"]
    permissions = [Permission("role-1", {Permission.READ})]
    properties = {"prop-name-1": "prop-value-1", "prop-name-2": "prop-value-2"}
    metadata_values_1 = {"meta-name-1": "meta-value-1", "meta-name-2": "meta-value-2"}
    metadata_values_2 = {"meta-name-1": "meta-value-1", "meta-name-2": "meta-value-3"}
    metadata_1 = Metadata(collections=collections,
                          permissions=permissions,
                          properties=properties,
                          quality=1,
                          metadata_values=metadata_values_1)
    metadata_2 = Metadata(collections=collections,
                          permissions=permissions,
                          properties=properties,
                          quality=1,
                          metadata_values=metadata_values_2)
    assert metadata_1 != metadata_2
    assert metadata_1.__hash__() != metadata_2.__hash__()


def test_copy(metadata):
    cp = copy.copy(metadata)
    assert cp is not metadata
    assert cp == metadata


def test_get_collections_when_exists():
    collections = ["collection-1", "collection-2"]
    metadata = Metadata(collections=collections)
    assert metadata.collections().sort() == collections.sort()


def test_get_collections_when_empty():
    metadata = Metadata()
    assert metadata.collections() == []


def test_get_permissions_when_exists():
    permission_1 = Permission("role-1", {Permission.READ})
    permission_2 = Permission("role-2", {Permission.READ, Permission.UPDATE})
    metadata = Metadata(permissions=[permission_1, permission_2])
    __assert_permissions_are_equal(metadata.permissions(), [permission_1, permission_2])


def test_get_permissions_when_empty():
    metadata = Metadata()
    assert metadata.permissions() == []


def test_get_properties_when_exists():
    properties = {"prop-name-1": "prop-value-1", "prop-name-2": "prop-value-2"}
    metadata = Metadata(properties=properties)
    assert metadata.properties() == properties


def test_get_properties_when_empty():
    metadata = Metadata()
    assert metadata.properties() == {}


def test_get_quality_when_exists():
    quality = 1
    metadata = Metadata(quality=quality)
    assert metadata.quality() == quality


def test_get_quality_when_empty():
    metadata = Metadata()
    assert metadata.quality() is None


def test_get_metadata_values_when_exists():
    metadata_values = {"meta-name-1": "meta-value-1", "meta-name-2": "meta-value-2"}
    metadata = Metadata(metadata_values=metadata_values)
    assert metadata.metadata_values() == metadata_values


def test_get_metadata_values_when_empty():
    metadata = Metadata()
    assert metadata.metadata_values() == {}


def test_set_quality():
    metadata = Metadata()
    success = metadata.set_quality(1)
    assert success is True
    assert metadata.quality() == 1

    success = metadata.set_quality(2)
    assert success is True
    assert metadata.quality() == 2


def test_set_quality_when_not_int():
    metadata = Metadata()
    success = metadata.set_quality("1")
    assert success is False
    assert metadata.quality() is None


def test_add_collection():
    metadata = Metadata()
    success = metadata.add_collection("collection-1")
    assert success is True
    assert metadata.collections() == ["collection-1"]

    success = metadata.add_collection("collection-2")
    assert success is True
    assert metadata.collections() == ["collection-1", "collection-2"]


def test_add_collection_when_exists():
    metadata = Metadata(collections=["collection-1"])
    success = metadata.add_collection("collection-1")
    assert success is False
    assert metadata.collections() == ["collection-1"]


def test_add_none_collection():
    metadata = Metadata(collections=["collection-1"])
    success = metadata.add_collection(None)
    assert success is False
    assert metadata.collections() == ["collection-1"]


def test_add_blank_collection():
    metadata = Metadata(collections=["collection-1"])
    success = metadata.add_collection(" \n")
    assert success is False
    assert metadata.collections() == ["collection-1"]


def test_add_permission():
    permission_1 = Permission("role-1", {Permission.READ})
    permission_2 = Permission("role-2", {Permission.READ, Permission.UPDATE})
    metadata = Metadata()
    success = metadata.add_permission("role-1", Permission.READ)
    assert success is True
    __assert_permissions_are_equal(metadata.permissions(), [permission_1])

    success = metadata.add_permission("role-2", Permission.READ)
    assert success is True
    success = metadata.add_permission("role-2", Permission.UPDATE)
    assert success is True
    __assert_permissions_are_equal(metadata.permissions(), [permission_1, permission_2])


def test_add_permission_when_exists():
    permission = Permission("role-1", {Permission.READ})
    metadata = Metadata(permissions=[permission])
    success = metadata.add_permission("role-1", Permission.READ)
    assert success is False
    __assert_permissions_are_equal(metadata.permissions(), [permission])


def test_add_permission_with_none_role():
    permission = Permission("role-1", {Permission.READ})
    metadata = Metadata(permissions=[permission])
    success = metadata.add_permission(None, Permission.UPDATE)
    assert success is False
    __assert_permissions_are_equal(metadata.permissions(), [permission])


def test_add_permission_with_none_capability():
    permission = Permission("role-1", {Permission.READ})
    metadata = Metadata(permissions=[permission])
    success = metadata.add_permission("role-1", None)
    assert success is False
    __assert_permissions_are_equal(metadata.permissions(), [permission])


def test_put_property():
    metadata = Metadata()
    metadata.put_property("prop-name-1", "prop-value-1")
    assert metadata.properties() == {
        "prop-name-1": "prop-value-1",
    }

    metadata.put_property("prop-name-2", "prop-value-2")
    assert metadata.properties() == {
        "prop-name-1": "prop-value-1",
        "prop-name-2": "prop-value-2",
    }


def test_put_property_when_exists():
    metadata = Metadata(properties={"prop-name-1": "prop-value-1"})
    metadata.put_property("prop-name-1", "prop-value-2")
    assert metadata.properties() == {
        "prop-name-1": "prop-value-2",
    }


def test_put_none_property():
    metadata = Metadata(properties={"prop-name-1": "prop-value-1"})
    metadata.put_property("prop-name-1", None)
    assert metadata.properties() == {
        "prop-name-1": "prop-value-1",
    }


def test_put_metadata_value():
    metadata = Metadata()
    metadata.put_metadata_value("meta-name-1", "meta-value-1")
    assert metadata.metadata_values() == {
        "meta-name-1": "meta-value-1",
    }

    metadata.put_metadata_value("meta-name-2", "meta-value-2")
    assert metadata.metadata_values() == {
        "meta-name-1": "meta-value-1",
        "meta-name-2": "meta-value-2",
    }


def test_put_metadata_value_when_exists():
    metadata = Metadata(metadata_values={"meta-name-1": "meta-value-1"})
    metadata.put_metadata_value("meta-name-1", "meta-value-2")
    assert metadata.metadata_values() == {
        "meta-name-1": "meta-value-2",
    }


def test_put_none_metadata_value():
    metadata = Metadata(metadata_values={"meta-name-1": "meta-value-1"})
    metadata.put_metadata_value("meta-name-1", None)
    assert metadata.metadata_values() == {
        "meta-name-1": "meta-value-1",
    }


def test_remove_collection():
    metadata = Metadata(collections=["collection-1", "collection-2"])
    success = metadata.remove_collection("collection-1")
    assert success is True
    assert metadata.collections() == ["collection-2"]

    success = metadata.remove_collection("collection-2")
    assert success is True
    assert metadata.collections() == []


def test_remove_collection_when_does_not_exist():
    metadata = Metadata(collections=["collection-1"])
    success = metadata.remove_collection("collection-2")
    assert success is False
    assert metadata.collections() == ["collection-1"]


def test_remove_permission():
    permissions = [
        Permission("role-1", {Permission.READ}),
        Permission("role-2", {Permission.READ, Permission.UPDATE}),
    ]
    metadata = Metadata(permissions=permissions)
    success = metadata.remove_permission("role-2", Permission.READ)
    assert success is True
    __assert_permissions_are_equal(metadata.permissions(), [
        Permission("role-1", {Permission.READ}),
        Permission("role-2", {Permission.UPDATE}),
    ])

    success = metadata.remove_permission("role-2", Permission.UPDATE)
    assert success is True
    __assert_permissions_are_equal(metadata.permissions(), [
        Permission("role-1", {Permission.READ}),
    ])

    success = metadata.remove_permission("role-1", Permission.READ)
    assert success is True
    assert metadata.permissions() == []


def test_remove_permission_when_does_not_exist():
    permission = Permission("role-1", {Permission.READ})
    metadata = Metadata(permissions=[permission])
    success = metadata.remove_permission("role-2", Permission.READ)
    assert success is False
    __assert_permissions_are_equal(metadata.permissions(), [permission])

    success = metadata.remove_permission("role-1", Permission.UPDATE)
    assert success is False
    __assert_permissions_are_equal(metadata.permissions(), [permission])


def test_remove_permission_when_none():
    permission = Permission("role-1", {Permission.READ})
    metadata = Metadata(permissions=[permission])
    success = metadata.remove_permission(None, Permission.READ)
    assert success is False
    __assert_permissions_are_equal(metadata.permissions(), [permission])

    success = metadata.remove_permission("role-1", None)
    assert success is False
    __assert_permissions_are_equal(metadata.permissions(), [permission])


def test_remove_property():
    properties = {"prop-name-1": "prop-value-1", "prop-name-2": "prop-value-2"}
    metadata = Metadata(properties=properties)
    success = metadata.remove_property("prop-name-1")
    assert success is True
    assert metadata.properties() == {
        "prop-name-2": "prop-value-2",
    }

    success = metadata.remove_property("prop-name-2")
    assert success is True
    assert metadata.properties() == {}


def test_remove_property_when_does_not_exist():
    metadata = Metadata(properties={"prop-name-1": "prop-value-1"})
    success = metadata.remove_property("prop-name-2")
    assert success is False
    assert metadata.properties() == {
        "prop-name-1": "prop-value-1",
    }


def test_remove_metadata_value():
    metadata_values = {"meta-name-1": "meta-value-1", "meta-name-2": "meta-value-2"}
    metadata = Metadata(metadata_values=metadata_values)
    success = metadata.remove_metadata_value("meta-name-1")
    assert success is True
    assert metadata.metadata_values() == {
        "meta-name-2": "meta-value-2",
    }

    success = metadata.remove_metadata_value("meta-name-2")
    assert success is True
    assert metadata.metadata_values() == {}


def test_remove_metadata_value_when_does_not_exist():
    metadata = Metadata(metadata_values={"meta-name-1": "meta-value-1"})
    success = metadata.remove_metadata_value("meta-name-2")
    assert success is False
    assert metadata.metadata_values() == {
        "meta-name-1": "meta-value-1",
    }


def test_duplicated_collections():
    collections = ["collection-1", "collection-1"]
    metadata = Metadata(collections=collections)
    assert metadata.collections() == ["collection-1"]


def test_duplicated_permissions():
    permission_1 = Permission("role-1", {Permission.READ})
    permission_2 = Permission("role-1", {Permission.READ})
    permission_3 = Permission("role-1", {Permission.READ, Permission.UPDATE})
    permission_4 = Permission("role-2", {Permission.READ, Permission.UPDATE})
    permissions = [permission_1, permission_2, permission_3, permission_4]
    metadata = Metadata(permissions=permissions)
    __assert_permissions_are_equal(metadata.permissions(), [permission_1, permission_4])


def test_properties_with_none_values():
    properties = {
        "prop-name-1": "prop-value-1",
        "prop-name-2": None,
        "prop-name-3": "prop-value-1",
        "prop-name-4": None,
    }
    metadata = Metadata(properties=properties)
    assert metadata.properties() == {
        "prop-name-1": "prop-value-1",
        "prop-name-3": "prop-value-1",
    }


def test_properties_with_non_string_values():
    properties = {
        "prop-name-1": [1, 2, 3],
        "prop-name-2": {"nested-key": 0.5},
        "prop-name-3": Permission("custom-role", {Permission.READ}),
        "prop-name-4": True,
    }
    metadata = Metadata(properties=properties)
    assert metadata.properties() == {
        "prop-name-1": "[1, 2, 3]",
        "prop-name-2": "{'nested-key': 0.5}",
        "prop-name-3": "Permission(role_name='custom-role', capabilities={'read'})",
        "prop-name-4": "True",
    }


def test_metadata_values_with_none_values():
    metadata_values = {
        "meta-name-1": "meta-value-1",
        "meta-name-2": None,
        "meta-name-3": "meta-value-3",
        "meta-name-4": None,
    }
    metadata = Metadata(metadata_values=metadata_values)
    assert metadata.metadata_values() == {
        "meta-name-1": "meta-value-1",
        "meta-name-3": "meta-value-3",
    }


def test_metadata_values_stringified():
    metadata_values = {
        "meta-name-1": [1, 2, 3],
        "meta-name-2": {"nested-key": 0.5},
        "meta-name-3": Permission("custom-role", {Permission.READ}),
        "meta-name-4": True,
    }
    metadata = Metadata(metadata_values=metadata_values)
    assert metadata.metadata_values() == {
        "meta-name-1": "[1, 2, 3]",
        "meta-name-2": "{'nested-key': 0.5}",
        "meta-name-3": "Permission(role_name='custom-role', capabilities={'read'})",
        "meta-name-4": "True",
    }


def test_to_json(metadata):
    metadata_json = metadata.to_json()
    collections = metadata_json.get("collections")
    permissions = metadata_json.get("permissions")
    properties = metadata_json.get("properties")
    quality = metadata_json.get("quality")
    metadata_values = metadata_json.get("metadataValues")

    assert list(metadata_json.keys()) == [
        "collections", "permissions", "properties", "quality", "metadataValues"]
    assert collections.sort() == ["collection-1", "collection-2"].sort()
    assert permissions in [
        [{"role-name": "role-1", "capabilities": [Permission.READ]},
         {"role-name": "role-2", "capabilities": [Permission.READ, Permission.UPDATE]}],
        [{"role-name": "role-1", "capabilities": [Permission.READ]},
         {"role-name": "role-2", "capabilities": [Permission.UPDATE, Permission.READ]}],
        [{"role-name": "role-2", "capabilities": [Permission.READ, Permission.UPDATE]},
         {"role-name": "role-1", "capabilities": [Permission.READ]}],
        [{"role-name": "role-2", "capabilities": [Permission.UPDATE, Permission.READ]},
         {"role-name": "role-1", "capabilities": [Permission.READ]}],
    ]
    assert properties == {"prop-name-1": "prop-value-1", "prop-name-2": "prop-value-2"}
    assert quality == 1
    assert metadata_values == {
        "meta-name-1": "meta-value-1",
        "meta-name-2": "meta-value-2",
    }


def test_to_json_string(metadata):
    metadata_json_string = metadata.to_json_string()
    assert "\n" not in metadata_json_string
    assert ('"collections": ["collection-1", "collection-2"]' in metadata_json_string or
            '"collections": ["collection-2", "collection-1"]' in metadata_json_string)
    assert (('"permissions": ['
             '{"role-name": "role-2", '
             '"capabilities": ["read", "update"]}, '
             '{"role-name": "role-1", '
             '"capabilities": ["read"]}]') in metadata_json_string or
            ('"permissions": ['
             '{"role-name": "role-1", '
             '"capabilities": ["read"]}, '
             '{"role-name": "role-2", '
             '"capabilities": ["read", "update"]}]') in metadata_json_string or
            ('"permissions": ['
             '{"role-name": "role-2", '
             '"capabilities": ["update", "read"]}, '
             '{"role-name": "role-1", '
             '"capabilities": ["read"]}]') in metadata_json_string or
            ('"permissions": ['
             '{"role-name": "role-1", '
             '"capabilities": ["read"]}, '
             '{"role-name": "role-2", '
             '"capabilities": ["update", "read"]}]') in metadata_json_string)
    assert (('"properties": '
             '{"prop-name-1": "prop-value-1", '
             '"prop-name-2": "prop-value-2"}') in metadata_json_string or
            ('"properties": '
             '{"prop-name-2": "prop-value-2", '
             '"prop-name-1": "prop-value-1"}') in metadata_json_string)
    assert '"quality": 1' in metadata_json_string
    assert (('"metadataValues": '
             '{"meta-name-1": "meta-value-1", '
             '"meta-name-2": "meta-value-2"}') in metadata_json_string or
            ('"metadataValues": '
             '{"meta-name-2": "meta-value-2", '
             '"meta-name-1": "meta-value-1"}') in metadata_json_string)


def test_to_json_string_with_indent(metadata):
    metadata_json_string = metadata.to_json_string(indent=4)
    assert "{\n" in metadata_json_string
    assert '    "collections": [\n' in metadata_json_string
    assert ('        "collection-1"\n' in metadata_json_string or
            '        "collection-1",\n' in metadata_json_string)
    assert ('        "collection-2"\n' in metadata_json_string or
            '        "collection-2",\n' in metadata_json_string)
    assert "    ],\n" in metadata_json_string
    assert '    "permissions": [\n' in metadata_json_string
    assert "        {\n" in metadata_json_string
    assert ('            "role-name": "role-1"\n' in metadata_json_string or
            '            "role-name": "role-1",\n' in metadata_json_string)
    assert '            "capabilities": [\n' in metadata_json_string
    assert '                "read"\n' in metadata_json_string
    assert ("            ]\n" in metadata_json_string or
            '            "],\n' in metadata_json_string)
    assert ("        }\n" in metadata_json_string or
            '        "},\n' in metadata_json_string)
    assert "        {\n" in metadata_json_string
    assert ('            "role-name": "role-2"\n' in metadata_json_string or
            '            "role-name": "role-2",\n' in metadata_json_string)
    assert '            "capabilities": [\n' in metadata_json_string
    assert ('                "read"\n' in metadata_json_string or
            '                "read",\n' in metadata_json_string)
    assert ('                "update"\n' in metadata_json_string or
            '                "update",\n' in metadata_json_string)
    assert ("            ]\n" in metadata_json_string or
            '            "],\n' in metadata_json_string)
    assert ("        }\n" in metadata_json_string or
            '        "},\n' in metadata_json_string)
    assert "    ],\n" in metadata_json_string
    assert '"properties": {\n' in metadata_json_string
    assert ('        "prop-name-1": "prop-value-1"\n' in metadata_json_string or
            '        "prop-name-1": "prop-value-1",\n' in metadata_json_string)
    assert ('        "prop-name-2": "prop-value-2"\n' in metadata_json_string or
            '        "prop-name-2": "prop-value-2",\n' in metadata_json_string)
    assert ("    },\n" in metadata_json_string or
            "    }\n" in metadata_json_string)
    assert ('    "quality": 1\n' in metadata_json_string or
            '    "quality": 1,\n' in metadata_json_string)
    assert '    "metadataValues": {\n' in metadata_json_string
    assert ('        "meta-name-1": "meta-value-1"\n' in metadata_json_string or
            '        "meta-name-1": "meta-value-1",\n' in metadata_json_string)
    assert ('        "meta-name-2": "meta-value-2"\n' in metadata_json_string or
            '        "meta-name-2": "meta-value-2",\n' in metadata_json_string)
    assert ("    }\n" in metadata_json_string or
            "    },\n" in metadata_json_string)
    assert "}" in metadata_json_string


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
    assert len(permission_elements) == 3
    for permission_element in permission_elements:
        assert permission_element.tag == "rapi:permission"
        assert permission_element.attrib == {}
        assert len(list(permission_element)) == 2

        permission_role_name = permission_element.find("rapi:role-name")
        assert permission_role_name is not None
        assert permission_role_name.attrib == {}
        assert len(list(permission_role_name)) == 0
        assert permission_role_name.text in ["role-1", "role-2"]

        permission_capability = permission_element.find("rapi:capability")
        assert permission_capability is not None
        assert permission_capability.attrib == {}
        assert len(list(permission_capability)) == 0
        if permission_role_name.tag == "role-1":
            assert permission_capability.text == "read"
        else:
            assert permission_capability.text in ["read", "update"]

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
        assert metadata_value_element.attrib in [
            {"key": "meta-name-1"},
            {"key": "meta-name-2"},
        ]
        assert len(list(metadata_value_element)) == 0
        assert metadata_value_element.text in ["meta-value-1", "meta-value-2"]


def test_to_xml_string(metadata):
    metadata_xml_string = metadata.to_xml_string()
    expected_lines = [
        "<?xml version='1.0' encoding='utf-8'?>\n",
        '<rapi:metadata xmlns:rapi="http://marklogic.com/rest-api">',
        "<rapi:collections>",
        "<rapi:collection>collection-1</rapi:collection>",
        "<rapi:collection>collection-2</rapi:collection>",
        "</rapi:collections>",
        "<rapi:permissions>",
        "<rapi:permission>",
        "<rapi:role-name>role-1</rapi:role-name><rapi:capability>read</rapi:capability>",
        "</rapi:permission>",
        "<rapi:permission>",
        "<rapi:role-name>role-2</rapi:role-name><rapi:capability>read</rapi:capability>",
        "</rapi:permission>",
        "<rapi:permission>",
        "<rapi:role-name>role-2</rapi:role-name><rapi:capability>update</rapi:capability>",
        "</rapi:permission>",
        "</rapi:permissions>",
        '<prop:properties xmlns:prop="http://marklogic.com/xdmp/property">',
        "<prop-name-1>prop-value-1</prop-name-1>",
        "<prop-name-2>prop-value-2</prop-name-2>",
        "</prop:properties>",
        "<rapi:quality>1</rapi:quality>",
        "<rapi:metadata-values>",
        '<rapi:metadata-value key="meta-name-1">meta-value-1</rapi:metadata-value>',
        '<rapi:metadata-value key="meta-name-2">meta-value-2</rapi:metadata-value>',
        "</rapi:metadata-values>",
        "</rapi:metadata>",
    ]
    for line in expected_lines:
        assert line in metadata_xml_string


def test_to_xml_string_with_indent(metadata):
    metadata_xml_string = metadata.to_xml_string(indent=4)
    expected_lines = [
        '<?xml version="1.0" encoding="utf-8"?>\n',
        '<rapi:metadata xmlns:rapi="http://marklogic.com/rest-api">\n',
        "    <rapi:collections>\n",
        "        <rapi:collection>collection-1</rapi:collection>\n",
        "        <rapi:collection>collection-2</rapi:collection>\n",
        "    </rapi:collections>\n",
        "    <rapi:permissions>\n",
        "        <rapi:permission>\n",
        "            <rapi:role-name>role-1</rapi:role-name>\n",
        "            <rapi:capability>read</rapi:capability>\n",
        "        </rapi:permission>\n",
        "        <rapi:permission>\n",
        "            <rapi:role-name>role-2</rapi:role-name>\n",
        "            <rapi:capability>read</rapi:capability>\n",
        "        </rapi:permission>\n",
        "        <rapi:permission>\n",
        "            <rapi:role-name>role-2</rapi:role-name>\n",
        "            <rapi:capability>update</rapi:capability>\n",
        "        </rapi:permission>\n",
        "    </rapi:permissions>\n",
        '    <prop:properties xmlns:prop="http://marklogic.com/xdmp/property">\n',
        "        <prop-name-1>prop-value-1</prop-name-1>\n",
        "        <prop-name-2>prop-value-2</prop-name-2>\n",
        "    </prop:properties>\n",
        "    <rapi:quality>1</rapi:quality>\n",
        "    <rapi:metadata-values>\n",
        ('        <rapi:metadata-value key="meta-name-1">meta-value-1'
         '</rapi:metadata-value>\n'),
        ('        <rapi:metadata-value key="meta-name-2">meta-value-2'
         '</rapi:metadata-value>\n'),
        "    </rapi:metadata-values>\n",
        "</rapi:metadata>\n",
    ]
    for line in expected_lines:
        assert line in metadata_xml_string
