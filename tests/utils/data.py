from __future__ import annotations

import json
import zlib
from dataclasses import dataclass
from typing import Any

from mlclient.models.calls import DocumentsBodyPart


@dataclass(frozen=True)
class MetadataSpec:
    """
    A lightweight specification object used **only for building multipart
    metadata representations**, mainly in tests.

    The purpose of this class is to explicitly control **which metadata fields
    are included** in a multipart request/response.

    Semantic rules:
    - A field set to None means: the corresponding metadata element
      MUST NOT be included in the multipart payload at all.
    - A field set to an empty value ([], {}, 0) means: the metadata element
      MUST be included, even if empty.

    This allows generating multipart payloads that contain only a subset
    of document metadata (e.g. collections only, or properties only),
    which is not possible with the Metadata class, as Metadata always
    serializes all metadata fields.

    IMPORTANT:
    - This class is NOT a replacement for Metadata.
    - It exists to preserve fine-grained control over multipart metadata
      composition, primarily for test builders and low-level API simulations.
    """

    collections: list[str] | None = None
    permissions: list[Any] | None = None
    properties: dict[str, Any] | None = None
    quality: int | None = None
    metadata_values: dict[str, Any] | None = None

    def to_payload(
        self,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if self.collections is not None:
            payload["collections"] = self.collections
        if self.permissions is not None:
            payload["permissions"] = self.permissions
        if self.properties is not None:
            payload["properties"] = self.properties
        if self.quality is not None:
            payload["quality"] = self.quality
        if self.metadata_values is not None:
            payload["metadataValues"] = self.metadata_values
        return payload

    def with_full_defaults(
        self,
    ) -> MetadataSpec:
        return MetadataSpec(
            collections=self.get_or_default(self.collections, []),
            permissions=self.get_or_default(self.permissions, []),
            properties=self.get_or_default(self.properties, {}),
            quality=self.get_or_default(self.quality, 0),
            metadata_values=self.get_or_default(self.metadata_values, {}),
        )

    @staticmethod
    def get_or_default(
        value: Any,
        default: Any,
    ) -> Any:
        return value if value is not None else default


def xml_doc_body_part(
    uri: str = "/some/dir/doc1.xml",
    content: bytes = b'<?xml version="1.0" encoding="UTF-8"?>\n<root/>',
):
    return doc_content_body_part("xml", uri, "application/xml", content)


def json_doc_body_part(
    uri: str = "/some/dir/doc1.json",
    content: bytes = b'{"root":{"child":"data"}}',
):
    return doc_content_body_part("json", uri, "application/json", content)


def text_doc_body_part(
    uri: str = "/some/dir/doc1.xqy",
    content_type: str = "application/vnd.marklogic-xdmp",
    content: bytes = b'xquery version "1.0-ml";\n\nfn:current-date()',
):
    return doc_content_body_part("text", uri, content_type, content)


def binary_doc_body_part(
    uri: str = "/some/dir/doc1.zip",
    content_type: str = "application/zip",
    content: bytes = zlib.compress(b'xquery version "1.0-ml";\n\nfn:current-date()'),
):
    return doc_content_body_part("binary", uri, content_type, content)


def doc_content_body_part(
    doc_type: str,
    uri: str,
    content_type: str,
    content: bytes,
) -> DocumentsBodyPart:
    return DocumentsBodyPart(
        **{
            "content-type": content_type,
            "content-disposition": "attachment; "
            f'filename="{uri}"; '
            "category=content; "
            f"format={doc_type}",
            "content": content,
        },
    )


def doc_full_metadata_body_part(
    uri: str,
    metadata: MetadataSpec,
    *,
    metadata_category: bool = False,
) -> DocumentsBodyPart:
    return doc_metadata_body_part(
        uri,
        metadata.with_full_defaults(),
        metadata_category=metadata_category,
    )


def doc_metadata_body_part(
    uri: str,
    metadata: MetadataSpec,
    *,
    metadata_category: bool = False,
) -> DocumentsBodyPart:
    payload = metadata.to_payload()
    content = json.dumps(payload).encode("utf-8")
    category_part = _category_part(payload, metadata_category=metadata_category)

    return DocumentsBodyPart(
        **{
            "content-type": "application/json",
            "content-disposition": "attachment; "
            f'filename="{uri}"; '
            f"{category_part}; "
            "format=json",
            "content": content,
        },
    )


def _category_part(
    payload: dict[str, Any],
    *,
    metadata_category: bool,
) -> str:
    if metadata_category and len(payload) == 5:
        return "category=metadata"

    key_to_category = {"metadataValues": "metadata-values"}
    return "; ".join(f"category={key_to_category.get(k, k)}" for k in payload)
