import json
import re
import xml.etree.ElementTree as ElemTree
from xml.dom import minidom


class Metadata:

    __COLLECTIONS_KEY = "collections"
    __PERMISSIONS_KEY = "permissions"
    __PROPERTIES_KEY = "properties"
    __QUALITY_KEY = "quality"
    __METADATA_VALUES_KEY = "metadataValues"

    __METADATA_TAG = "rapi:metadata"
    __COLLECTIONS_TAG = "rapi:collections"
    __COLLECTION_TAG = "rapi:collection"
    __PERMISSIONS_TAG = "rapi:permissions"
    __PERMISSION_TAG = "rapi:permission"
    __PROPERTIES_TAG = "prop:properties"
    __QUALITY_TAG = "rapi:quality"
    __METADATA_VALUES_TAG = "rapi:metadata-values"
    __METADATA_VALUE_TAG = "rapi:metadata-value"
    __KEY_ATTR = "key"

    __RAPI_NS_PREFIX = "xmlns:rapi"
    __PROP_NS_PREFIX = "xmlns:prop"
    __RAPI_NS_URI = "http://marklogic.com/rest-api"
    __PROP_NS_URI = "http://marklogic.com/xdmp/property"

    def __init__(self, collections: set = None, permissions: set = None, properties: dict = None,
                 quality: int = None, metadata_values: dict = None) -> None:
        self.__metadata = {
            self.__COLLECTIONS_KEY: collections if collections else set(),
            self.__PERMISSIONS_KEY: permissions if permissions else set(),
            self.__PROPERTIES_KEY: self.__get_clean_dict(properties) if properties else dict(),
            self.__QUALITY_KEY: quality,
            self.__METADATA_VALUES_KEY: self.__get_clean_dict(metadata_values) if metadata_values else dict()
        }

    def collections(self) -> set:
        return self.__metadata[self.__COLLECTIONS_KEY].copy()

    def permissions(self) -> set:
        return self.__metadata[self.__PERMISSIONS_KEY].copy()

    def properties(self) -> dict:
        return self.__metadata[self.__PROPERTIES_KEY].copy()

    def quality(self) -> int:
        return self.__metadata[self.__QUALITY_KEY]

    def metadata_values(self) -> dict:
        return self.__metadata[self.__METADATA_VALUES_KEY].copy()

    def set_quality(self, quality: int) -> bool:
        allow = isinstance(quality, int)
        if allow:
            self.__metadata[self.__QUALITY_KEY] = quality
        return allow

    def add_collection(self, collection: str) -> bool:
        allow = collection is not None and not re.search("^\\s*$", collection) and collection not in self.collections()
        if allow:
            self.__metadata[self.__COLLECTIONS_KEY].add(collection)
        return allow

    def add_permission(self, permission: str) -> bool:
        allow = permission is not None and not re.search("^\\s*$", permission) and permission not in self.permissions()
        if allow:
            self.__metadata[self.__PERMISSIONS_KEY].add(permission)
        return allow

    def put_property(self, property_name: str, property_value: str) -> None:
        if property_name and property_value:
            self.__metadata[self.__PROPERTIES_KEY][property_name] = property_value

    def put_metadata_value(self, name: str, value: str) -> None:
        if name and value:
            self.__metadata[self.__METADATA_VALUES_KEY][name] = value

    def remove_collection(self, collection: str) -> bool:
        allow = collection is not None and collection in self.collections()
        if allow:
            self.__metadata[self.__COLLECTIONS_KEY].remove(collection)
        return allow

    def remove_permission(self, permission: str) -> bool:
        allow = permission is not None and permission in self.permissions()
        if allow:
            self.__metadata[self.__PERMISSIONS_KEY].remove(permission)
        return allow

    def remove_property(self, property_name: str) -> bool:
        return self.__metadata[self.__PROPERTIES_KEY].pop(property_name, None) is not None

    def remove_metadata_value(self, name: str) -> bool:
        return self.__metadata[self.__METADATA_VALUES_KEY].pop(name, None) is not None

    def to_json(self) -> dict:
        return self.__metadata.copy()

    def to_json_string(self, indent: int = None) -> str:
        return json.dumps(self.__metadata, cls=SetEncoder, indent=indent)

    def to_xml(self) -> ElemTree.ElementTree:
        root = ElemTree.Element(self.__METADATA_TAG,
                                attrib={self.__RAPI_NS_PREFIX: self.__RAPI_NS_URI})

        collections_element = ElemTree.SubElement(root, self.__COLLECTIONS_TAG)
        for collection in self.collections():
            collection_element = ElemTree.SubElement(collections_element, self.__COLLECTION_TAG)
            collection_element.text = collection

        permissions_element = ElemTree.SubElement(root, self.__PERMISSIONS_TAG)
        for permission in self.permissions():
            permission_element = ElemTree.SubElement(permissions_element, self.__PERMISSION_TAG)
            permission_element.text = permission

        properties_element = ElemTree.SubElement(root, self.__PROPERTIES_TAG,
                                                 attrib={self.__PROP_NS_PREFIX: self.__PROP_NS_URI})
        for property_name, property_value in self.properties().items():
            property_element = ElemTree.SubElement(properties_element, property_name)
            property_element.text = property_value

        quality_element = ElemTree.SubElement(root, self.__QUALITY_TAG)
        quality_element.text = str(self.quality())

        metadata_values_element = ElemTree.SubElement(root, self.__METADATA_VALUES_TAG)
        for metadata_name, metadata_value in self.metadata_values().items():
            metadata_element = ElemTree.SubElement(metadata_values_element, self.__METADATA_VALUE_TAG,
                                                   attrib={self.__KEY_ATTR: metadata_name})
            metadata_element.text = metadata_value

        return ElemTree.ElementTree(root)

    def to_xml_string(self, indent: int = None) -> str:
        metadata_xml = self.to_xml().getroot()
        if indent is None:
            return ElemTree.tostring(metadata_xml,
                                     encoding="utf-8",
                                     method="xml",
                                     xml_declaration=True).decode('ascii')
        else:
            metadata_xml_string = ElemTree.tostring(metadata_xml)
            return minidom.parseString(metadata_xml_string).toprettyxml(indent=" " * indent,
                                                                        encoding="utf-8").decode('ascii')

    @staticmethod
    def __get_clean_dict(source_dict):
        return {k: v for k, v in source_dict.items() if v is not None}


class Permission:

    READ = "read"
    INSERT = "insert"
    UPDATE = "update"
    UPDATE_NODE = "update-node"
    EXECUTE = "execute"

    __CAPABILITIES = {READ, INSERT, UPDATE, UPDATE_NODE, EXECUTE}

    def __init__(self, role_name: str, capabilities: set):
        self.__role_name = role_name
        self.__capabilities = {cap for cap in capabilities if cap in self.__CAPABILITIES}

    def role_name(self):
        return self.__role_name

    def capabilities(self):
        return self.__capabilities.copy()

    def add_capability(self, capability):
        allow = capability is not None and capability in self.__CAPABILITIES and capability not in self.capabilities()
        if allow:
            self.__capabilities.add(capability)
        return allow

    def remove_capability(self, capability: str) -> bool:
        allow = capability is not None and capability in self.capabilities()
        if allow:
            self.__capabilities.remove(capability)
        return allow

    def __eq__(self, other):
        return (isinstance(other, Permission) and
                self.__role_name == other.__role_name and
                self.__capabilities == other.__capabilities)

    def __hash__(self):
        items = list(self.__capabilities)
        items.append(self.__role_name)
        return hash(tuple(items))


class SetEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)
