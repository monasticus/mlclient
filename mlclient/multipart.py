"""The Multipart/Mixed module.

It provides functions and a data class for building and parsing
multipart/mixed HTTP messages:
    * MultipartPart
        A single part of a multipart/mixed message.
    * encode_multipart_mixed
        Encode parts into a multipart/mixed body.
    * decode_multipart_mixed
        Parse a multipart/mixed body into parts.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass
class MultipartPart:
    """A single part of a multipart/mixed message."""

    headers: dict[str, str]
    content: bytes

    @property
    def text(self) -> str:
        """Decode content to string using the charset from Content-Type."""
        charset = "utf-8"
        content_type = self.headers.get("Content-Type", "")
        for param in content_type.split(";"):
            param = param.strip()
            if param.lower().startswith("charset="):
                charset = param.split("=", 1)[1].strip().strip('"')
        return self.content.decode(charset)


def encode_multipart_mixed(
    parts: list[MultipartPart],
    boundary: str | None = None,
) -> tuple[bytes, str]:
    """Encode parts into a multipart/mixed body.

    Parameters
    ----------
    parts : list[MultipartPart]
        The parts to encode
    boundary : str | None
        An optional boundary string; generated if not provided

    Returns
    -------
    tuple[bytes, str]
        A tuple of (body_bytes, content_type_header)
    """
    if boundary is None:
        boundary = uuid.uuid4().hex
    segments = []
    for part in parts:
        segment = f"--{boundary}\r\n".encode()
        for name, value in part.headers.items():
            segment += f"{name}: {value}\r\n".encode()
        segment += b"\r\n"
        segment += part.content
        segment += b"\r\n"
        segments.append(segment)
    body = b"".join(segments) + f"--{boundary}--\r\n".encode()
    content_type = f"multipart/mixed; boundary={boundary}"
    return body, content_type


def decode_multipart_mixed(
    content: bytes,
    content_type: str,
) -> list[MultipartPart]:
    """Parse a multipart/mixed body into parts.

    Parameters
    ----------
    content : bytes
        The raw multipart body
    content_type : str
        The Content-Type header value containing the boundary

    Returns
    -------
    list[MultipartPart]
        The parsed parts
    """
    boundary = _extract_boundary(content_type)
    delimiter = f"\r\n--{boundary}".encode()
    pieces = content.split(delimiter)
    first = f"--{boundary}\r\n".encode()
    if pieces[0].startswith(first):
        pieces[0] = pieces[0][len(first):]
    else:
        pieces.pop(0)
    # Last piece is "--\r\n" (closing marker)
    pieces.pop()
    parts = []
    for piece in pieces:
        if piece.startswith(b"\r\n"):
            piece = piece[2:]
        header_block, _, body = piece.partition(b"\r\n\r\n")
        headers = {}
        for line in header_block.split(b"\r\n"):
            name, _, value = line.partition(b": ")
            headers[name.decode()] = value.decode()
        parts.append(MultipartPart(headers=headers, content=body))
    return parts


def _extract_boundary(content_type: str) -> str:
    for param in content_type.split(";"):
        param = param.strip()
        if param.startswith("boundary="):
            return param.split("=", 1)[1].strip().strip('"')
    msg = f"No boundary found in Content-Type: {content_type}"
    raise ValueError(msg)
