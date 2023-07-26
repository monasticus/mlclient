from __future__ import annotations

import copy
import json
import logging
import re
import xml.etree.ElementTree as ElemTree
from enum import Enum
from xml.dom import minidom

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """An enumeration class representing document types.

    Attributes
    ----------
    XML : str
        XML document type
    JSON : str
        JSON document type
    BINARY : str
        Binary document type
    TEXT : str
        Text document type
    """

    XML = "xml"
    JSON = "json"
    BINARY = "binary"
    TEXT = "text"


class Document:
    """A class representing a single MarkLogic document.

    Methods
    -------
    uri() -> str
        Return a document URI.
    doc_type() -> DocumentType
        Return a document type.
    metadata() -> Metadata
        Return a document metadata.
    is_temporal() -> bool
        Return the temporal flag.
    """

    def __init__(
            self,
            uri: str | None = None,
            doc_type: DocumentType = DocumentType.XML,
            metadata: Metadata | None = None,
            is_temporal: bool = False,
    ):
        """Initialize Document instance.

        Parameters
        ----------
        uri : str
            A document URI
        doc_type : DocumentType
            A document type
        metadata : Metadata
            A document metadata
        is_temporal : bool
            The temporal flag
        """
        self._uri = self._get_non_blank_uri(uri)
        self._doc_type = doc_type
        self._metadata = metadata
        self._is_temporal = is_temporal

    def uri(
            self,
    ) -> str:
        """Return a document URI."""
        return self._uri

    def doc_type(
            self,
    ) -> DocumentType:
        """Return a document type."""
        return self._doc_type

    def metadata(
            self,
    ) -> Metadata:
        """Return a document metadata."""
        return copy.copy(self._metadata)

    def is_temporal(
            self,
    ) -> bool:
        """Return the temporal flag."""
        return self._is_temporal

    @staticmethod
    def _get_non_blank_uri(
            uri: str
    ) -> str | None:
        """Return URI or None when blank."""
        return uri if uri is not None and not re.search("^\\s*$", uri) else None


class Metadata:

    _COLLECTIONS_KEY = "collections"
    _PERMISSIONS_KEY = "permissions"
    _PROPERTIES_KEY = "properties"
    _QUALITY_KEY = "quality"
    _METADATA_VALUES_KEY = "metadataValues"

    _METADATA_TAG = "rapi:metadata"
    _COLLECTIONS_TAG = "rapi:collections"
    _COLLECTION_TAG = "rapi:collection"
    _PERMISSIONS_TAG = "rapi:permissions"
    _PERMISSION_TAG = "rapi:permission"
    _ROLE_NAME_TAG = "rapi:role-name"
    _CAPABILITY_TAG = "rapi:capability"
    _PROPERTIES_TAG = "prop:properties"
    _QUALITY_TAG = "rapi:quality"
    _METADATA_VALUES_TAG = "rapi:metadata-values"
    _METADATA_VALUE_TAG = "rapi:metadata-value"
    _KEY_ATTR = "key"

    _RAPI_NS_PREFIX = "xmlns:rapi"
    _PROP_NS_PREFIX = "xmlns:prop"
    _RAPI_NS_URI = "http://marklogic.com/rest-api"
    _PROP_NS_URI = "http://marklogic.com/xdmp/property"

    def __init__(
            self,
            collections: list | None = None,
            permissions: list | None = None,
            properties: dict | None = None,
            quality: int | None = None,
            metadata_values: dict | None = None,
    ):
        self._collections = list(set(collections)) if collections else list()
        self._permissions = self._get_clean_permissions(permissions)
        self._properties = self._get_clean_dict(properties)
        self._quality = quality
        self._metadata_values = self._get_clean_dict(metadata_values)

    def __eq__(
            self,
            other,
    ) -> bool:
        collections_diff = set(self._collections).difference(set(other.collections()))
        permissions_diff = set(self._permissions).difference(set(other.permissions()))
        return (isinstance(other, Metadata) and
                collections_diff == set() and
                permissions_diff == set() and
                self._properties == other.properties() and
                self._quality == other.quality() and
                self._metadata_values == other.metadata_values())

    def __hash__(
            self,
    ) -> int:
        items = self.collections()
        items.extend(self.permissions())
        items.append(self.quality())
        items.append(frozenset(self.properties().items()))
        items.append(frozenset(self.metadata_values().items()))
        return hash(tuple(items))

    def __copy__(
            self,
    ) -> Metadata:
        return Metadata(
            collections=self.collections(),
            permissions=self.permissions(),
            properties=self.properties(),
            quality=self.quality(),
            metadata_values=self.metadata_values())

    def collections(
            self,
    ) -> list:
        return self._collections.copy()

    def permissions(
            self,
    ) -> list:
        return [copy.copy(perm) for perm in self._permissions]

    def properties(
            self,
    ) -> dict:
        return self._properties.copy()

    def quality(
            self,
    ) -> int:
        return self._quality

    def metadata_values(
            self,
    ) -> dict:
        return self._metadata_values.copy()

    def set_quality(
            self,
            quality: int,
    ) -> bool:
        allow = isinstance(quality, int)
        if allow:
            self._quality = quality
        return allow

    def add_collection(
            self,
            collection: str,
    ) -> bool:
        allow = (collection is not None and
                 not re.search("^\\s*$", collection) and
                 collection not in self.collections())
        if allow:
            self._collections.append(collection)
        return allow

    def add_permission(
            self,
            role_name: str,
            capability: str,
    ) -> bool:
        allow = role_name is not None and capability is not None
        if allow:
            permission = self._get_permission_for_role(self._permissions, role_name)
            if permission is not None:
                return permission.add_capability(capability)
            else:
                self._permissions.append(Permission(role_name, {capability}))
                return True
        return allow

    def put_property(
            self,
            property_name: str,
            property_value: str,
    ):
        if property_name and property_value:
            self._properties[property_name] = property_value

    def put_metadata_value(
            self,
            name: str,
            value: str,
    ):
        if name and value:
            self._metadata_values[name] = value

    def remove_collection(
            self,
            collection: str,
    ) -> bool:
        allow = collection is not None and collection in self.collections()
        if allow:
            self._collections.remove(collection)
        return allow

    def remove_permission(
            self,
            role_name: str,
            capability: str = None,
    ) -> bool:
        allow = role_name is not None and capability is not None
        if allow:
            permission = self._get_permission_for_role(self._permissions, role_name)
            allow = permission is not None
            if allow:
                success = permission.remove_capability(capability)
                if len(permission.capabilities()) == 0:
                    self._permissions.remove(permission)
                return success
            return allow
        return allow

    def remove_property(
            self,
            property_name: str,
    ) -> bool:
        return self._properties.pop(property_name, None) is not None

    def remove_metadata_value(
            self,
            name: str,
    ) -> bool:
        return self._metadata_values.pop(name, None) is not None

    def to_json(
            self,
    ) -> dict:
        return {
            self._COLLECTIONS_KEY: self.collections(),
            self._PERMISSIONS_KEY: [p.to_json() for p in self._permissions],
            self._PROPERTIES_KEY: self.properties(),
            self._QUALITY_KEY: self.quality(),
            self._METADATA_VALUES_KEY: self._metadata_values
        }

    def to_json_string(
            self,
            indent: int | None = None,
    ) -> str:
        return json.dumps(self.to_json(), cls=MetadataEncoder, indent=indent)

    def to_xml_string(self, indent: int = None) -> str:
        metadata_xml = self.to_xml().getroot()
        if indent is None:
            metadata_str = ElemTree.tostring(
                metadata_xml,
                encoding="utf-8",
                method="xml",
                xml_declaration=True)
        else:
            metadata_xml_string = ElemTree.tostring(metadata_xml)
            metadata_xml_minidom = minidom.parseString(metadata_xml_string)
            metadata_str = metadata_xml_minidom.toprettyxml(
                indent=" " * indent,
                encoding="utf-8")
        return metadata_str.decode("ascii")

    def to_xml(
            self,
    ) -> ElemTree.ElementTree:
        attrs = {self._RAPI_NS_PREFIX: self._RAPI_NS_URI}
        root = ElemTree.Element(self._METADATA_TAG, attrib=attrs)

        self._to_xml_collections(root)
        self._to_xml_permissions(root)
        self._to_xml_properties(root)
        self._to_xml_quality(root)
        self._to_xml_metadata_values(root)
        return ElemTree.ElementTree(root)

    def _to_xml_collections(
            self,
            root: ElemTree.Element,
    ):
        parent = ElemTree.SubElement(root, self._COLLECTIONS_TAG)
        for collection in self.collections():
            child = ElemTree.SubElement(parent, self._COLLECTION_TAG)
            child.text = collection

    def _to_xml_permissions(
            self,
            root: ElemTree.Element,
    ):
        permissions = ElemTree.SubElement(root, self._PERMISSIONS_TAG)
        for perm in self._permissions:
            for cap in perm.capabilities():
                permission = ElemTree.SubElement(permissions, self._PERMISSION_TAG)
                role_name = ElemTree.SubElement(permission, self._ROLE_NAME_TAG)
                capability = ElemTree.SubElement(permission, self._CAPABILITY_TAG)
                role_name.text = perm.role_name()
                capability.text = cap

    def _to_xml_properties(
            self,
            root: ElemTree.Element,
    ):
        attrs = {self._PROP_NS_PREFIX: self._PROP_NS_URI}
        properties = ElemTree.SubElement(root, self._PROPERTIES_TAG, attrib=attrs)
        for prop_name, prop_value in self.properties().items():
            property_ = ElemTree.SubElement(properties, prop_name)
            property_.text = prop_value

    def _to_xml_quality(
            self,
            root: ElemTree.Element,
    ):
        quality = ElemTree.SubElement(root, self._QUALITY_TAG)
        quality.text = str(self.quality())

    def _to_xml_metadata_values(
            self,
            root: ElemTree.Element,
    ):
        values = ElemTree.SubElement(root, self._METADATA_VALUES_TAG)
        for metadata_name, metadata_value in self.metadata_values().items():
            attrs = {self._KEY_ATTR: metadata_name}
            child = ElemTree.SubElement(values, self._METADATA_VALUE_TAG, attrib=attrs)
            child.text = metadata_value

    @classmethod
    def _get_clean_permissions(
            cls,
            source_permissions: list | None,
    ):
        permissions = []
        if source_permissions is None:
            return permissions

        for permission in source_permissions:
            role_name = permission.role_name()
            existing_perm = cls._get_permission_for_role(permissions, role_name)
            if existing_perm is None:
                permissions.append(permission)
            else:
                logger.warning(
                    "Ignoring permission [%s]: role [%s] is already used in [%s]",
                    permission, role_name, existing_perm)
        return permissions

    @staticmethod
    def _get_permission_for_role(
            permissions: list,
            role_name: str,
    ):
        return next(filter(lambda p: p.role_name() == role_name, permissions), None)

    @staticmethod
    def _get_clean_dict(
            source_dict: dict | None,
    ):
        if not source_dict:
            return dict()
        return {k: str(v) for k, v in source_dict.items() if v is not None}


class Permission:

    READ = "read"
    INSERT = "insert"
    UPDATE = "update"
    UPDATE_NODE = "update-node"
    EXECUTE = "execute"

    _CAPABILITIES = {READ, INSERT, UPDATE, UPDATE_NODE, EXECUTE}

    def __init__(
            self,
            role_name: str,
            capabilities: set,
    ):
        self._role_name = role_name
        self._capabilities = {cap for cap in capabilities if cap in self._CAPABILITIES}

    def __eq__(
            self,
            other,
    ) -> bool:
        return (isinstance(other, Permission) and
                self._role_name == other._role_name and
                self._capabilities == other._capabilities)

    def __hash__(
            self,
    ) -> int:
        items = list(self._capabilities)
        items.append(self._role_name)
        return hash(tuple(items))

    def __repr__(
            self,
    ) -> str:
        return (f"Permission("
                f"role_name='{self._role_name}', "
                f"capabilities={self._capabilities})")

    def role_name(
            self,
    ) -> str:
        return self._role_name

    def capabilities(
            self,
    ) -> set:
        return self._capabilities.copy()

    def add_capability(
            self,
            capability: str,
    ) -> bool:
        allow = (capability is not None and
                 capability in self._CAPABILITIES and
                 capability not in self.capabilities())
        if allow:
            self._capabilities.add(capability)
        return allow

    def remove_capability(
            self,
            capability: str,
    ) -> bool:
        allow = (capability is not None and
                 capability in self.capabilities())
        if allow:
            self._capabilities.remove(capability)
        return allow

    def to_json(
            self,
    ):
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
