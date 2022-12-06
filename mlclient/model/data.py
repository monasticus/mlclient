import copy
import json
import logging
import re
import xml.etree.ElementTree as ElemTree
from enum import Enum
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
    __ROLE_NAME_TAG = "rapi:role-name"
    __CAPABILITY_TAG = "rapi:capability"
    __PROPERTIES_TAG = "prop:properties"
    __QUALITY_TAG = "rapi:quality"
    __METADATA_VALUES_TAG = "rapi:metadata-values"
    __METADATA_VALUE_TAG = "rapi:metadata-value"
    __KEY_ATTR = "key"

    __RAPI_NS_PREFIX = "xmlns:rapi"
    __PROP_NS_PREFIX = "xmlns:prop"
    __RAPI_NS_URI = "http://marklogic.com/rest-api"
    __PROP_NS_URI = "http://marklogic.com/xdmp/property"

    def __init__(self, collections: list = None, permissions: list = None, properties: dict = None,
                 quality: int = None, metadata_values: dict = None) -> None:
        self.__logger = logging.getLogger(__name__)
        self.__collections = list(set(collections)) if collections else list()
        self.__permissions = self.__get_clean_permissions(permissions)
        self.__properties = self.__get_clean_dict(properties) if properties else dict()
        self.__quality = quality
        self.__metadata_values = self.__get_clean_dict(metadata_values) if metadata_values else dict()

    def __eq__(self, other):
        return (isinstance(other, Metadata) and
                set(self.__collections).difference(set(other.collections())) == set() and
                set(self.__permissions).difference(set(other.permissions())) == set() and
                self.__properties == other.properties() and
                self.__quality == other.quality() and
                self.__metadata_values == other.metadata_values())

    def __hash__(self):
        items = self.collections()
        items.extend(self.permissions())
        items.append(self.quality())
        items.append(frozenset(self.properties().items()))
        items.append(frozenset(self.metadata_values().items()))
        return hash(tuple(items))

    def __copy__(self):
        return Metadata(collections=self.collections(),
                        permissions=self.permissions(),
                        properties=self.properties(),
                        quality=self.quality(),
                        metadata_values=self.metadata_values())

    def collections(self) -> list:
        return self.__collections.copy()

    def permissions(self) -> list:
        return [copy.copy(perm) for perm in self.__permissions]

    def properties(self) -> dict:
        return self.__properties.copy()

    def quality(self) -> int:
        return self.__quality

    def metadata_values(self) -> dict:
        return self.__metadata_values.copy()

    def set_quality(self, quality: int) -> bool:
        allow = isinstance(quality, int)
        if allow:
            self.__quality = quality
        return allow

    def add_collection(self, collection: str) -> bool:
        allow = collection is not None and not re.search("^\\s*$", collection) and collection not in self.collections()
        if allow:
            self.__collections.append(collection)
        return allow

    def add_permission(self, role_name: str, capability: str) -> bool:
        allow = role_name is not None and capability is not None
        if allow:
            permission = self.__get_permission_for_role(role_name)
            if permission is not None:
                return permission.add_capability(capability)
            else:
                self.__permissions.append(Permission(role_name, {capability}))
                return True
        return allow

    def put_property(self, property_name: str, property_value: str) -> None:
        if property_name and property_value:
            self.__properties[property_name] = property_value

    def put_metadata_value(self, name: str, value: str) -> None:
        if name and value:
            self.__metadata_values[name] = value

    def remove_collection(self, collection: str) -> bool:
        allow = collection is not None and collection in self.collections()
        if allow:
            self.__collections.remove(collection)
        return allow

    def remove_permission(self, role_name: str, capability: str = None) -> bool:
        allow = role_name is not None and capability is not None
        if allow:
            permission = self.__get_permission_for_role(role_name)
            allow = permission is not None
            if allow:
                success = permission.remove_capability(capability)
                if len(permission.capabilities()) == 0:
                    self.__permissions.remove(permission)
                return success
            return allow
        return allow

    def remove_property(self, property_name: str) -> bool:
        return self.__properties.pop(property_name, None) is not None

    def remove_metadata_value(self, name: str) -> bool:
        return self.__metadata_values.pop(name, None) is not None

    def to_json(self) -> dict:
        return {
            self.__COLLECTIONS_KEY: self.collections(),
            self.__PERMISSIONS_KEY: [p.to_json() for p in self.__permissions],
            self.__PROPERTIES_KEY: self.properties(),
            self.__QUALITY_KEY: self.quality(),
            self.__METADATA_VALUES_KEY: self.__metadata_values
        }

    def to_json_string(self, indent: int = None) -> str:
        return json.dumps(self.to_json(), cls=MetadataEncoder, indent=indent)

    def to_xml(self) -> ElemTree.ElementTree:
        root = ElemTree.Element(self.__METADATA_TAG,
                                attrib={self.__RAPI_NS_PREFIX: self.__RAPI_NS_URI})

        collections_element = ElemTree.SubElement(root, self.__COLLECTIONS_TAG)
        for collection in self.collections():
            collection_element = ElemTree.SubElement(collections_element, self.__COLLECTION_TAG)
            collection_element.text = collection

        permissions_element = ElemTree.SubElement(root, self.__PERMISSIONS_TAG)
        for permission in self.__permissions:
            for capability in permission.capabilities():
                permission_element = ElemTree.SubElement(permissions_element, self.__PERMISSION_TAG)
                role_name_element = ElemTree.SubElement(permission_element, self.__ROLE_NAME_TAG)
                role_name_element.text = permission.role_name()
                capability_element = ElemTree.SubElement(permission_element, self.__CAPABILITY_TAG)
                capability_element.text = capability

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

    def __get_permission_for_role(self, role_name: str):
        return next((perm for perm in self.__permissions if perm.role_name() == role_name), None)

    def __get_clean_permissions(self, source_permissions: list):
        if source_permissions is None:
            return []
        permissions = []
        roles = []
        for permission in source_permissions:
            role_name = permission.role_name()
            if role_name not in roles:
                roles.append(role_name)
                permissions.append(permission)
            else:
                self.__logger.warning("Ignoring permission [%s]: role [%s] is already used in [%s]",
                                      permission,
                                      role_name,
                                      next(filter(lambda p: p.role_name() == role_name, permissions)))
        return permissions

    @staticmethod
    def __get_clean_dict(source_dict: dict):
        return {k: str(v) for k, v in source_dict.items() if v is not None}


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

    def __eq__(self, other):
        return (isinstance(other, Permission) and
                self.__role_name == other.__role_name and
                self.__capabilities == other.__capabilities)

    def __hash__(self):
        items = list(self.__capabilities)
        items.append(self.__role_name)
        return hash(tuple(items))

    def __repr__(self):
        return f"Permission(role_name='{self.__role_name}', capabilities={self.__capabilities})"

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

    def to_json(self):
        return {
            "role-name": self.role_name(),
            "capabilities": list(self.capabilities())
        }


class MetadataEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, Permission):
            return obj.to_json()
        return json.JSONEncoder.default(self, obj)


class DocumentType(Enum):
    XML = "xml"
    JSON = "json"
    BINARY = "binary"
    TEXT = "text"


class Document:

    def __init__(self, uri: str = None, doc_type: DocumentType = DocumentType.XML,
                 metadata: Metadata = None, is_temporal: bool = False):
        self.__uri = self.__get_non_blank_uri(uri)
        self.__doc_type = doc_type
        self.__metadata = metadata
        self.__is_temporal = is_temporal

    def uri(self) -> str:
        return self.__uri

    def doc_type(self) -> DocumentType:
        return self.__doc_type

    def metadata(self) -> Metadata:
        return copy.copy(self.__metadata)

    def is_temporal(self) -> bool:
        return self.__is_temporal

    @staticmethod
    def __get_non_blank_uri(uri):
        return uri if uri is not None and not re.search("^\\s*$", uri) else None
