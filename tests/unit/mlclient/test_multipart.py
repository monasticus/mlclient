import pytest

from mlclient.multipart import (
    MultipartPart,
    decode_multipart_mixed,
    encode_multipart_mixed,
)


class TestEncodeMultipartMixed:
    def test_encode_empty(self):
        body, content_type = encode_multipart_mixed([])
        assert content_type.startswith("multipart/mixed; boundary=")
        boundary = content_type.split("boundary=")[1]
        assert body == f"--{boundary}--\r\n".encode()

    def test_encode_single_part(self):
        part = MultipartPart(
            headers={"Content-Type": "text/plain"},
            content=b"hello",
        )
        body, content_type = encode_multipart_mixed([part])
        boundary = content_type.split("boundary=")[1]
        expected = (
            f"--{boundary}\r\n"
            "Content-Type: text/plain\r\n"
            "\r\n"
            "hello\r\n"
            f"--{boundary}--\r\n"
        ).encode()
        assert body == expected

    def test_encode_multiple_parts(self):
        parts = [
            MultipartPart(
                headers={"Content-Type": "text/plain"},
                content=b"part1",
            ),
            MultipartPart(
                headers={"Content-Type": "application/json"},
                content=b'{"key": "value"}',
            ),
        ]
        body, content_type = encode_multipart_mixed(parts)
        boundary = content_type.split("boundary=")[1]
        assert f"--{boundary}\r\n".encode() in body
        assert b"part1" in body
        assert b'{"key": "value"}' in body

    def test_encode_binary_content(self):
        binary = bytes(range(256))
        part = MultipartPart(
            headers={"Content-Type": "application/octet-stream"},
            content=binary,
        )
        body, _ = encode_multipart_mixed([part])
        assert binary in body

    def test_encode_custom_boundary(self):
        part = MultipartPart(
            headers={"Content-Type": "text/plain"},
            content=b"test",
        )
        body, content_type = encode_multipart_mixed([part], boundary="myboundary")
        assert content_type == "multipart/mixed; boundary=myboundary"
        assert b"--myboundary\r\n" in body
        assert b"--myboundary--\r\n" in body

    def test_encode_multiple_headers(self):
        part = MultipartPart(
            headers={
                "Content-Disposition": 'attachment; filename="/doc.json"',
                "Content-Type": "application/json",
            },
            content=b'{"data": true}',
        )
        body, _ = encode_multipart_mixed([part])
        assert b'Content-Disposition: attachment; filename="/doc.json"\r\n' in body
        assert b"Content-Type: application/json\r\n" in body


class TestDecodeMultipartMixed:
    def test_decode_single_part(self):
        raw = (
            b"--boundary\r\n"
            b"Content-Type: text/plain\r\n"
            b"\r\n"
            b"hello\r\n"
            b"--boundary--\r\n"
        )
        parts = decode_multipart_mixed(raw, "multipart/mixed; boundary=boundary")
        assert len(parts) == 1
        assert parts[0].headers == {"Content-Type": "text/plain"}
        assert parts[0].content == b"hello"

    def test_decode_multiple_parts(self):
        raw = (
            b"--boundary\r\n"
            b"Content-Type: text/plain\r\n"
            b"\r\n"
            b"part1\r\n"
            b"--boundary\r\n"
            b"Content-Type: application/json\r\n"
            b"\r\n"
            b'{"key": "value"}\r\n'
            b"--boundary--\r\n"
        )
        parts = decode_multipart_mixed(raw, "multipart/mixed; boundary=boundary")
        assert len(parts) == 2
        assert parts[0].content == b"part1"
        assert parts[1].content == b'{"key": "value"}'

    def test_decode_binary_content(self):
        binary = bytes(range(256))
        raw = (
            b"--boundary\r\n"
            b"Content-Type: application/octet-stream\r\n"
            b"\r\n"
            + binary
            + b"\r\n"
            b"--boundary--\r\n"
        )
        parts = decode_multipart_mixed(raw, "multipart/mixed; boundary=boundary")
        assert parts[0].content == binary

    def test_decode_missing_boundary(self):
        with pytest.raises(ValueError, match="No boundary found"):
            decode_multipart_mixed(b"", "multipart/mixed")

    def test_decode_with_preamble(self):
        raw = (
            b"preamble text\r\n"
            b"--boundary\r\n"
            b"Content-Type: text/plain\r\n"
            b"\r\n"
            b"data\r\n"
            b"--boundary--\r\n"
        )
        parts = decode_multipart_mixed(raw, "multipart/mixed; boundary=boundary")
        assert len(parts) == 1
        assert parts[0].content == b"data"

    def test_decode_quoted_boundary(self):
        raw = (
            b"--myboundary\r\n"
            b"Content-Type: text/plain\r\n"
            b"\r\n"
            b"data\r\n"
            b"--myboundary--\r\n"
        )
        parts = decode_multipart_mixed(
            raw,
            'multipart/mixed; boundary="myboundary"',
        )
        assert len(parts) == 1
        assert parts[0].content == b"data"


class TestMultipartPart:
    def test_text_default_charset(self):
        part = MultipartPart(
            headers={"Content-Type": "text/plain"},
            content=b"hello",
        )
        assert part.text == "hello"

    def test_text_explicit_charset(self):
        part = MultipartPart(
            headers={"Content-Type": "text/plain; charset=utf-8"},
            content=b"hello",
        )
        assert part.text == "hello"

    def test_text_latin1_charset(self):
        part = MultipartPart(
            headers={"Content-Type": "text/plain; charset=latin-1"},
            content="caf\xe9".encode("latin-1"),
        )
        assert part.text == "caf\xe9"


class TestRoundtrip:
    def test_roundtrip_text_parts(self):
        original = [
            MultipartPart(
                headers={"Content-Type": "text/plain", "X-Primitive": "string"},
                content=b"hello world",
            ),
            MultipartPart(
                headers={"Content-Type": "application/json"},
                content=b'{"key": "value"}',
            ),
        ]
        body, content_type = encode_multipart_mixed(original)
        decoded = decode_multipart_mixed(body, content_type)
        assert len(decoded) == len(original)
        for orig, dec in zip(original, decoded):
            assert orig.headers == dec.headers
            assert orig.content == dec.content

    def test_roundtrip_binary(self):
        binary = bytes(range(256))
        original = [
            MultipartPart(
                headers={"Content-Type": "application/octet-stream"},
                content=binary,
            ),
        ]
        body, content_type = encode_multipart_mixed(original)
        decoded = decode_multipart_mixed(body, content_type)
        assert decoded[0].content == binary
