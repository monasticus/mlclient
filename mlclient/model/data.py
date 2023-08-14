"""The ML Data module.

It exports 5 classes:
    * DocumentType
        An enumeration class representing document types.
    * Document
        A class representing a single MarkLogic document.
    * Metadata
        A class representing MarkLogic's document metadata.
    * Permission:
        A class representing MarkLogic's document permission.
    * MetadataEncoder(json.JSONEncoder):
        A JSONEncoder subclass to dump Metadata to JSON accordingly.
"""
from __future__ import annotations

import copy
import json
import logging
import re
import xml.etree.ElementTree as ElemTree
from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Any, ClassVar
from xml.dom import minidom

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """An enumeration class representing document types."""

    XML: str = "xml"
    JSON: str = "json"
    BINARY: str = "binary"
    TEXT: str = "text"


class Document(metaclass=ABCMeta):
    """A class representing a single MarkLogic document."""

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

    @classmethod
    def __subclasshook__(
            cls,
            subclass: Document,
    ):
        """Verify if a subclass implements all abstract methods.

        Parameters
        ----------
        subclass : Document
            A Document subclass

        Returns
        -------
        bool
            True if the subclass includes the content property
        """
        return "content" in subclass.__dict__ and not callable(subclass.content)

    @property
    @abstractmethod
    def content(
            self,
    ) -> Any:
        """A document content.

        Returns
        -------
        Any
            A document's content
        """
        raise NotImplementedError

    @property
    def uri(
            self,
    ) -> str:
        """A document URI."""
        return self._uri

    @property
    def doc_type(
            self,
    ) -> DocumentType:
        """A document type."""
        return self._doc_type

    @property
    def metadata(
            self,
    ) -> Metadata:
        """A document metadata."""
        return copy.copy(self._metadata)

    @property
    def is_temporal(
            self,
    ) -> bool:
        """The temporal flag."""
        return self._is_temporal

    @staticmethod
    def _get_non_blank_uri(
            uri: str,
    ) -> str | None:
        """Return URI or None when blank."""
        return uri if uri is not None and not re.search("^\\s*$", uri) else None


class Metadata:
    """A class representing MarkLogic's document metadata."""

    _COLLECTIONS_KEY: str = "collections"
    _PERMISSIONS_KEY: str = "permissions"
    _PROPERTIES_KEY: str = "properties"
    _QUALITY_KEY: str = "quality"
    _METADATA_VALUES_KEY: str = "metadataValues"

    _METADATA_TAG: str = "rapi:metadata"
    _COLLECTIONS_TAG: str = "rapi:collections"
    _COLLECTION_TAG: str = "rapi:collection"
    _PERMISSIONS_TAG: str = "rapi:permissions"
    _PERMISSION_TAG: str = "rapi:permission"
    _ROLE_NAME_TAG: str = "rapi:role-name"
    _CAPABILITY_TAG: str = "rapi:capability"
    _PROPERTIES_TAG: str = "prop:properties"
    _QUALITY_TAG: str = "rapi:quality"
    _METADATA_VALUES_TAG: str = "rapi:metadata-values"
    _METADATA_VALUE_TAG: str = "rapi:metadata-value"
    _KEY_ATTR: str = "key"

    _RAPI_NS_PREFIX: str = "xmlns:rapi"
    _PROP_NS_PREFIX: str = "xmlns:prop"
    _RAPI_NS_URI: str = "http://marklogic.com/rest-api"
    _PROP_NS_URI: str = "http://marklogic.com/xdmp/property"

    def __init__(
            self,
            collections: list | None = None,
            permissions: list | None = None,
            properties: dict | None = None,
            quality: int | None = None,
            metadata_values: dict | None = None,
    ):
        """Initialize Metadata instance.

        Parameters
        ----------
        collections : list | None
            Document collections' list
        permissions : list | None
            Document permissions' list
        properties : dict | None
            Document's properties
        quality : int | None
            Document's quality
        metadata_values : dict | None
            Document's metadata values
        """
        self._collections = list(set(collections)) if collections else []
        self._permissions = self._get_clean_permissions(permissions)
        self._properties = self._get_clean_dict(properties)
        self._quality = quality
        self._metadata_values = self._get_clean_dict(metadata_values)

    def __eq__(
            self,
            other: Metadata,
    ) -> bool:
        """Verify if Metadata instances are equal.

        Parameters
        ----------
        other : Metadata
            A Metadata instance to compare

        Returns
        -------
        bool
            True if there's no difference between internal Metadata fields.
            Otherwise, False.
        """
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
        """Generate a hash value of a Metadata instance.

        Returns
        -------
        int
            A hash value generated using all internal Metadata fields.
        """
        items = self.collections()
        items.extend(self.permissions())
        items.append(self.quality())
        items.append(frozenset(self.properties().items()))
        items.append(frozenset(self.metadata_values().items()))
        return hash(tuple(items))

    def __copy__(
            self,
    ) -> Metadata:
        """Copy Metadata instance."""
        return Metadata(
            collections=self.collections(),
            permissions=self.permissions(),
            properties=self.properties(),
            quality=self.quality(),
            metadata_values=self.metadata_values())

    def collections(
            self,
    ) -> list:
        """Return document's collections."""
        return self._collections.copy()

    def permissions(
            self,
    ) -> list:
        """Return document's permissions."""
        return [copy.copy(perm) for perm in self._permissions]

    def properties(
            self,
    ) -> dict:
        """Return document's properties."""
        return self._properties.copy()

    def quality(
            self,
    ) -> int:
        """Return document's quality."""
        return self._quality

    def metadata_values(
            self,
    ) -> dict:
        """Return document's metadata values."""
        return self._metadata_values.copy()

    def set_quality(
            self,
            quality: int,
    ) -> bool:
        """Set document's quality.

        Parameters
        ----------
        quality : int
            A document's new quality

        Returns
        -------
        allow : bool
            True if value provided is an integer. Otherwise, False.
        """
        allow = isinstance(quality, int)
        if allow:
            self._quality = quality
        return allow

    def add_collection(
            self,
            collection: str,
    ) -> bool:
        """Assign a new collection to document.

        Parameters
        ----------
        collection : str
            A document's new collection

        Returns
        -------
        allow : bool
            True if the collection is non-blank value, and it does not appear already
            in document's collections. Otherwise, False.
        """
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
        """Assign a new permission to document.

        Parameters
        ----------
        role_name : str
            a permission's role name
        capability : str
            a permission's capability

        Returns
        -------
        bool
            True if there's no such capability assigned to this role already, and it is
            a correct one. Otherwise, False.
        """
        allow = role_name is not None and capability is not None
        if allow:
            permission = self._get_permission_for_role(self._permissions, role_name)
            if permission is not None:
                return permission.add_capability(capability)

            self._permissions.append(Permission(role_name, {capability}))
            return True
        return allow

    def put_property(
            self,
            name: str,
            value: str,
    ):
        """Assign a new property to document.

        Parameters
        ----------
        name : str
            A property name
        value : str
            A property value
        """
        if name and value:
            self._properties[name] = value

    def put_metadata_value(
            self,
            name: str,
            value: str,
    ):
        """Assign a new metadata value to document.

        Parameters
        ----------
        name : str
            A metadata name
        value : str
            A metadata value
        """
        if name and value:
            self._metadata_values[name] = value

    def remove_collection(
            self,
            collection: str,
    ) -> bool:
        """Remove a collection from document.

        Parameters
        ----------
        collection : str
            A document's collection

        Returns
        -------
        allow : bool
            True if the collection is assigned to the document. Otherwise, False.
        """
        allow = collection is not None and collection in self.collections()
        if allow:
            self._collections.remove(collection)
        return allow

    def remove_permission(
            self,
            role_name: str,
            capability: str,
    ) -> bool:
        """Remove a permission from document.

        Parameters
        ----------
        role_name : str
            A permission's role name
        capability : str
            A permission's capability

        Returns
        -------
        bool
            True if the capability is assigned to the role for a document.
            Otherwise, False.
        """
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
            name: str,
    ) -> bool:
        """Remove a property from document.

        Parameters
        ----------
        name : str
            A property name

        Returns
        -------
        bool
            True if the document has a property with such name. Otherwise, False.
        """
        return self._properties.pop(name, None) is not None

    def remove_metadata_value(
            self,
            name: str,
    ) -> bool:
        """Remove a metadata value from document.

        Parameters
        ----------
        name : str
            A metadata name

        Returns
        -------
        bool
            True if the document has a metadata with such name. Otherwise, False.
        """
        return self._metadata_values.pop(name, None) is not None

    def to_json_string(
            self,
            indent: int | None = None,
    ) -> str:
        """Return a stringified JSON representation of the Metadata instance.

        Parameters
        ----------
        indent : int | None
            A number of spaces per indent level

        Returns
        -------
        str
            Metadata in a stringified JSON representation
        """
        return json.dumps(self.to_json(), indent=indent)

    def to_json(
            self,
    ) -> dict:
        """Return a JSON representation of the Metadata instance."""
        return {
            self._COLLECTIONS_KEY: self.collections(),
            self._PERMISSIONS_KEY: [p.to_json() for p in self._permissions],
            self._PROPERTIES_KEY: self.properties(),
            self._QUALITY_KEY: self.quality(),
            self._METADATA_VALUES_KEY: self._metadata_values,
        }

    def to_xml_string(
            self,
            indent: int | None = None,
    ) -> str:
        """Return a stringified XML representation of the Metadata instance.

        Parameters
        ----------
        indent : int | None
            A number of spaces per indent level

        Returns
        -------
        str
            Metadata in a stringified XML representation
        """
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
        """Return an XML representation of the Metadata instance."""
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
        """Add collections node to Metadata root."""
        parent = ElemTree.SubElement(root, self._COLLECTIONS_TAG)
        for collection in self.collections():
            child = ElemTree.SubElement(parent, self._COLLECTION_TAG)
            child.text = collection

    def _to_xml_permissions(
            self,
            root: ElemTree.Element,
    ):
        """Add permissions node to Metadata root."""
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
        """Add properties node to Metadata root."""
        attrs = {self._PROP_NS_PREFIX: self._PROP_NS_URI}
        properties = ElemTree.SubElement(root, self._PROPERTIES_TAG, attrib=attrs)
        for prop_name, prop_value in self.properties().items():
            property_ = ElemTree.SubElement(properties, prop_name)
            property_.text = prop_value

    def _to_xml_quality(
            self,
            root: ElemTree.Element,
    ):
        """Add quality node to Metadata root."""
        quality = ElemTree.SubElement(root, self._QUALITY_TAG)
        quality.text = str(self.quality())

    def _to_xml_metadata_values(
            self,
            root: ElemTree.Element,
    ):
        """Add metadata values node to Metadata root."""
        values = ElemTree.SubElement(root, self._METADATA_VALUES_TAG)
        for metadata_name, metadata_value in self.metadata_values().items():
            attrs = {self._KEY_ATTR: metadata_name}
            child = ElemTree.SubElement(values, self._METADATA_VALUE_TAG, attrib=attrs)
            child.text = metadata_value

    @classmethod
    def _get_clean_permissions(
            cls,
            source_permissions: list | None,
    ) -> list:
        """Return permissions list without duplicates.

        If source permissions are None, it returns an empty list.

        Parameters
        ----------
        source_permissions : list | None
            Source permissions to clean out.

        Returns
        -------
        permissions : list
            A clean permissions list
        """
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
    ) -> Permission | None:
        """Return permissions assigned to the role provided.

        Parameters
        ----------
        permissions : list
            A permissions list
        role_name : str
            A role name

        Returns
        -------
        Permission | None
            A role's permission if exists. Otherwise, None.
        """
        return next(filter(lambda p: p.role_name() == role_name, permissions), None)

    @staticmethod
    def _get_clean_dict(
            source_dict: dict | None,
    ) -> dict:
        """Return a dictionary with stringified values and removed None values.

        If source dictionary are None, it returns an empty one.

        Parameters
        ----------
        source_dict : dict | None
            A source dictionary to clean out.

        Returns
        -------
        dict
            A clean dictionary
        """
        if not source_dict:
            return {}
        return {k: str(v) for k, v in source_dict.items() if v is not None}


class Permission:
    """A class representing MarkLogic's document permission."""

    READ: str = "read"
    INSERT: str = "insert"
    UPDATE: str = "update"
    UPDATE_NODE: str = "update-node"
    EXECUTE: str = "execute"

    _CAPABILITIES: ClassVar[tuple] = {READ, INSERT, UPDATE, UPDATE_NODE, EXECUTE}

    def __init__(
            self,
            role_name: str,
            capabilities: set,
    ):
        """Initialize a Permission instance.

        Parameters
        ----------
        role_name : str
            A role name
        capabilities : set
            Capabilities set
        """
        self._role_name = role_name
        self._capabilities = {cap for cap in capabilities if cap in self._CAPABILITIES}

    def __eq__(
            self,
            other: Permission,
    ) -> bool:
        """Verify if Permission instances are equal.

        Parameters
        ----------
        other : Permission
            A Permission instance to compare

        Returns
        -------
        bool
            True if there's no difference between internal Permission fields.
            Otherwise, False.
        """
        return (isinstance(other, Permission) and
                self._role_name == other._role_name and
                self._capabilities == other._capabilities)

    def __hash__(
            self,
    ) -> int:
        """Generate a hash value of a Permission instance.

        Returns
        -------
        int
            A hash value generated using all internal Permission fields.
        """
        items = list(self._capabilities)
        items.append(self._role_name)
        return hash(tuple(items))

    def __repr__(
            self,
    ) -> str:
        """Return a string representation of the Permission instance."""
        return (f"Permission("
                f"role_name='{self._role_name}', "
                f"capabilities={self._capabilities})")

    def role_name(
            self,
    ) -> str:
        """Return permission's role name."""
        return self._role_name

    def capabilities(
            self,
    ) -> set:
        """Return permission's capabilities."""
        return self._capabilities.copy()

    def add_capability(
            self,
            capability: str,
    ) -> bool:
        """Assign a new capability to the role.

        Parameters
        ----------
        capability : str
            a permission's capability

        Returns
        -------
        allow : bool
            True if there's no such capability assigned to this role already, and it is
            a correct one. Otherwise, False.
        """
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
        """Remove a capability from the role.

        Parameters
        ----------
        capability : str
            a permission's capability

        Returns
        -------
        allow : bool
            True if the capability is assigned to the role.
            Otherwise, False.
        """
        allow = (capability is not None and
                 capability in self.capabilities())
        if allow:
            self._capabilities.remove(capability)
        return allow

    def to_json(
            self,
    ) -> dict:
        """Return a JSON representation of the Permission instance."""
        return {
            "role-name": self.role_name(),
            "capabilities": list(self.capabilities()),
        }
