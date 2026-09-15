"""The ML Models types module.

It exports the following classes:
    * DocumentType
        An enumeration class representing document types.
    * Mimetype
        A class representing a mime type.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from mlclient.exceptions import InvalidLogTypeError


class DocumentType(Enum):
    """An enumeration class representing document types."""

    XML: str = "xml"
    JSON: str = "json"
    BINARY: str = "binary"
    TEXT: str = "text"


class Mimetype(BaseModel):
    """A class representing a mime type."""

    mime_type: str = Field(alias="mime-type")
    extensions: list[str]
    document_type: DocumentType = Field(alias="doc-type")


class LogType(Enum):
    """An enumeration class representing MarkLogic log types."""

    ERROR = "ErrorLog"
    ACCESS = "AccessLog"
    REQUEST = "RequestLog"
    AUDIT = "AuditLog"

    @staticmethod
    def get(
        logs_type: str,
    ) -> LogType:
        """Get a specific LogType enum for a string value."""
        if logs_type.lower() == "error":
            return LogType.ERROR
        if logs_type.lower() == "access":
            return LogType.ACCESS
        if logs_type.lower() == "request":
            return LogType.REQUEST
        if logs_type.lower() == "audit":
            return LogType.AUDIT
        msg = "Invalid log type! Allowed values are: error, access, request."
        raise InvalidLogTypeError(msg)

    def __lt__(
        self,
        other: LogType,
    ):
        """Compare LogTypes with LT operator."""
        return self.value < other.value
