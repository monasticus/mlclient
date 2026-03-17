from __future__ import annotations

import json
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Iterator, List, Sequence

import httpx
import respx
import urllib3
from httpx import Headers, Request, Response
from requests_toolbelt import MultipartDecoder
from requests_toolbelt.multipart.decoder import BodyPart
from respx import MockRouter, Route
from urllib3.fields import RequestField

from mlclient.constants import HEADER_X_WWW_FORM_URLENCODED
from mlclient.structures.calls import (
    Category,
    ContentDispositionSerializer,
    DocumentsBodyPart,
    DocumentsBodyPartType,
    DocumentsContentDisposition,
)


class MLMocker(metaclass=ABCMeta):
    @abstractmethod
    def with_url(self, url: str):
        raise NotImplementedError

    @abstractmethod
    def with_method(self, method: str):
        raise NotImplementedError

    @abstractmethod
    def with_request_param(self, name: str, value: str):
        raise NotImplementedError

    def with_request_content_type(self, content_type: str):
        self.with_request_header("Content-Type", content_type)

    @abstractmethod
    def with_request_header(self, name: str, value: str):
        raise NotImplementedError

    @abstractmethod
    def with_request_body(self, body: bytes | str | dict):
        raise NotImplementedError

    @abstractmethod
    def with_response_code(self, status_code: int):
        raise NotImplementedError

    def with_response_content_type(self, content_type: str):
        self.with_response_header("Content-Type", content_type)

    @abstractmethod
    def with_response_header(self, name: str, value: str):
        raise NotImplementedError

    def with_empty_response_body(self):
        self.with_response_body(b"")
        self.with_response_header("Content-Length", "0")

    @abstractmethod
    def with_response_body(self, body: bytes | str | dict):
        raise NotImplementedError

    @abstractmethod
    def with_response_body_part(
        self,
        x_primitive: str | None,
        body_part_content: Any,
        content_type: str | None = None,
    ):
        raise NotImplementedError

    @abstractmethod
    def with_response_documents_body_part(
        self,
        body_part: DocumentsBodyPart,
    ):
        raise NotImplementedError

    def mock_get(
        self,
    ):
        self.with_method("GET")
        return self.mock_response()

    def mock_delete(
        self,
    ):
        self.with_method("DELETE")
        return self.mock_response()

    def mock_post(
        self,
    ):
        self.with_method("POST")
        return self.mock_response()

    def mock_put(
        self,
    ):
        self.with_method("PUT")
        return self.mock_response()

    @abstractmethod
    def mock_response(
        self,
    ):
        raise NotImplementedError

    @staticmethod
    def error_logs_body(
        logs: list[tuple],
    ):
        logs_body = {"logfile": {}}
        if len(logs) > 0:
            logs_body["logfile"]["log"] = [
                {
                    "timestamp": log_tuple[0],
                    "level": log_tuple[1],
                    "message": log_tuple[2],
                }
                for log_tuple in logs
            ]
        return logs_body

    @staticmethod
    def non_error_logs_body(
        logs: list[str],
    ):
        logs_body = {"logfile": {}}
        if len(logs) > 0:
            logs_body["logfile"]["message"] = "\n".join(logs)
        return logs_body


@dataclass
class RespXRequest:
    name: str | None = None
    url: str = ""
    method: str = ""
    params: List[tuple] | None = None
    headers: Headers | None = None
    content: bytes | str | None = None
    data: dict | None = None
    json_: dict | None = None

    def as_kwargs(self) -> dict[str, Any]:
        kwargs = {
            "name": self.name,
            "url": self.url,
            "method": self.method,
            "params": self.params,
            "headers": self.headers,
            "content": self.content,
            "data": self.data,
            "json": self.json_,
        }
        return {key: value for key, value in kwargs.items() if value is not None}


@dataclass
class RespXResponse:
    status_code: int = -1
    headers: Headers | None = None
    content: bytes | str | None = None
    json_: dict | None = None
    body_parts: list[RequestField] | None = None

    def as_kwargs(self) -> dict[str, Any]:
        kwargs = {
            "status_code": self.status_code,
            "headers": self.headers,
            "content": self.content,
            "json": self.json_,
        }
        return {key: value for key, value in kwargs.items() if value is not None}


@dataclass
class RespXMock:
    request: RespXRequest = field(default_factory=RespXRequest)
    response: RespXResponse = field(default_factory=RespXResponse)
    side_effect: (
        Callable
        | Exception
        | type[Exception]
        | Sequence[Response | Exception | type[Exception]]
        | None
    ) = None


class MLRespXMocker(MLMocker):
    def __init__(self, use_router: bool = True, router_base_url: str | None = None):
        if use_router:
            self._mock = respx.mock(base_url=router_base_url, assert_all_called=False)
        else:
            self._mock = respx
        self._resp_mock = RespXMock()

    @property
    def router(self) -> MockRouter | None:
        if isinstance(self._mock, MockRouter):
            return self._mock
        return None

    def with_name(self, name: str):
        self._resp_mock.request.name = name

    def with_url(self, url: str):
        self._resp_mock.request.url = url

    def with_method(self, method: str):
        self._resp_mock.request.method = method

    def with_request_param(self, name: str, value: str):
        if value is not None:
            if not self._resp_mock.request.params:
                self._resp_mock.request.params = []
            self._resp_mock.request.params.append((name, value))

    def with_request_header(self, name: str, value: str):
        if value is not None:
            if not self._resp_mock.request.headers:
                self._resp_mock.request.headers = Headers()
            self._resp_mock.request.headers[name] = value

    def with_request_body(self, body: bytes | str | dict):
        if (
            self._resp_mock.request.headers.get("content-type")
            == HEADER_X_WWW_FORM_URLENCODED
        ):
            self._resp_mock.request.data = body
        elif isinstance(body, dict):
            self._resp_mock.request.json_ = body
        else:
            self._resp_mock.request.content = body

    def with_response_code(self, status_code: int):
        self._resp_mock.response.status_code = status_code

    def with_response_header(self, name: str, value: str):
        if value is not None:
            if not self._resp_mock.response.headers:
                self._resp_mock.response.headers = Headers()
            self._resp_mock.response.headers[name] = value

    def with_empty_response_body(self):
        self.with_response_body(b"")
        self.with_response_header("Content-Length", "0")

    def with_response_body(self, body: bytes | str | dict):
        if isinstance(body, dict):
            self._resp_mock.response.json_ = body
        else:
            self._resp_mock.response.content = body

    def with_response_body_part(
        self,
        x_primitive: str | None,
        body_part_content: Any,
        content_type: str | None = None,
    ):
        if not self._resp_mock.response.body_parts:
            self._resp_mock.response.body_parts = []

        if content_type is not None:
            ...
        elif x_primitive in ["array", "map"]:
            content_type = "application/json"
        elif x_primitive in ["document-node()", "element()"]:
            content_type = "application/xml"
        else:
            content_type = "text/plain"

        headers = {"Content-Type": content_type}
        if x_primitive is not None:
            headers["X-Primitive"] = x_primitive

        req_field = RequestField(
            name="--ignore--",
            data=body_part_content,
            headers=headers,
        )
        self._resp_mock.response.body_parts.append(req_field)

    def with_response_documents_body_part(
        self,
        body_part: DocumentsBodyPart,
    ):
        if not self._resp_mock.response.body_parts:
            self._resp_mock.response.body_parts = []

        data = body_part.content
        if isinstance(data, dict):
            data = json.dumps(data)
        content_disp = ContentDispositionSerializer.deserialize(
            body_part.content_disposition,
        )
        req_field = RequestField(
            name="--ignore--",
            data=data,
            headers={
                "Content-Disposition": content_disp,
                "Content-Type": body_part.content_type,
            },
        )
        self._resp_mock.response.body_parts.append(req_field)

    def with_get_side_effect(
        self,
        side_effect: (
            Callable
            | Exception
            | type[Exception]
            | Sequence[Response | Exception | type[Exception]]
        ),
    ) -> Route:
        self._resp_mock.side_effect = side_effect
        return self.mock_get()

    def with_post_side_effect(
        self,
        side_effect: (
            Callable
            | Exception
            | type[Exception]
            | Sequence[Response | Exception | type[Exception]]
        ),
    ) -> Route:
        self._resp_mock.side_effect = side_effect
        return self.mock_post()

    def mock_response(
        self,
    ) -> Route:
        if self._resp_mock.side_effect:
            route = self._mock.request(
                **self._resp_mock.request.as_kwargs(),
            )
            route.mock(side_effect=self._resp_mock.side_effect)
        else:
            self._validate()
            self._setup_response_body()
            route = self._mock.request(
                **self._resp_mock.request.as_kwargs(),
            )
            route.respond(**self._resp_mock.response.as_kwargs())
        self._resp_mock = RespXMock()
        return route

    def _validate(self):
        bodies = [
            body
            for body in [
                self._resp_mock.response.content,
                self._resp_mock.response.json_,
                self._resp_mock.response.body_parts,
            ]
            if body is not None
        ]
        if len(bodies) > 1:
            msg = "You can't set more than 1 response body"
            raise RuntimeError(msg)

    def _setup_response_body(self):
        if self._resp_mock.response.body_parts is not None:
            body, content_type = urllib3.encode_multipart_formdata(
                self._resp_mock.response.body_parts,
            )
            content_type = content_type.replace(
                "multipart/form-data",
                "multipart/mixed",
            )
            self.with_response_content_type(content_type)
            self._resp_mock.response.body_parts = None
            self._resp_mock.response.content = body


class MLDocumentsMocker:
    NON_EXISTING_TAG = "NON_EXISTING"

    def __init__(
        self,
        docs: Iterable[DocumentsBodyPart] | None = None,
    ):
        self._doc_body_parts = [] if docs is None else list(docs)

    @contextmanager
    def scoped(
        self,
        *,
        fresh: bool = True,
    ) -> Iterator[MLDocumentsMocker]:
        docs = self._doc_body_parts.copy()
        if fresh:
            self._doc_body_parts = []
        try:
            yield self
        finally:
            self._doc_body_parts = docs

    def mock_documents(
        self,
        docs: Iterable[DocumentsBodyPart],
    ):
        self.mock_document(*docs)

    def mock_document(
        self,
        *docs: DocumentsBodyPart,
    ):
        self._doc_body_parts.extend(docs)

    def get_documents_side_effect(
        self,
        request: Request,
    ) -> Response:
        uris = request.url.params.get_list("uri")
        category = request.url.params.get_list("category")
        if len(category) == 0:
            category = ["content"]

        if len(uris) == 1 and len(category) == 1:
            return self._build_single_part_response(uris[0], category)
        return self._build_multipart_response(uris, category)

    def post_documents_side_effect(
        self,
        request: Request,
    ) -> Response:
        body_parts = MultipartDecoder.from_response(request).parts
        if len(body_parts) == 1:
            body_part = body_parts[0]
            uri = self._get_content_disposition(body_part).filename
            if uri and self.NON_EXISTING_TAG in uri:
                return self._build_doc_not_found_error_post_response(uri, body_part)

        doc_objects = self._build_doc_objects(body_parts)
        return self._build_successful_post_response(doc_objects)

    def _build_single_part_response(
        self,
        uri: str,
        category: list[str],
    ) -> Response:
        body_parts = list(self._find_body_parts(uri, category))
        if len(body_parts) == 0:
            return self._build_no_document_error_get_response(uri)
        return self._build_successful_single_part_get_response(body_parts[0])

    def _build_multipart_response(
        self,
        uris: list[str],
        category: list[str],
    ) -> Response:
        form_data_fields = self._build_form_data_fields(uris, category)
        return self._build_successful_multipart_get_response(form_data_fields)

    def _build_form_data_fields(
        self,
        uris: list[str],
        category: list[str],
    ) -> list[RequestField]:
        return [
            self._build_form_data_field(body_part)
            for uri in uris
            for body_part in self._find_body_parts(uri, category)
            if body_part is not None
        ]

    @staticmethod
    def _build_form_data_field(
        body_part: DocumentsBodyPart,
    ) -> RequestField:
        data = body_part.content
        if isinstance(data, dict):
            data = json.dumps(data)
        content_disp = ContentDispositionSerializer.deserialize(
            body_part.content_disposition,
        )
        return RequestField(
            name="--ignore--",
            data=data,
            headers={
                "Content-Disposition": content_disp,
                "Content-Type": body_part.content_type,
            },
        )

    def _find_body_parts(
        self,
        uri: str,
        category: list[str],
    ) -> Iterable[DocumentsBodyPart]:
        return (
            part
            for part in self._doc_body_parts
            if self._match_body_part(uri, category, part)
        )

    @classmethod
    def _match_body_part(
        cls,
        uri: str,
        category: list[str],
        body_part: DocumentsBodyPart,
    ) -> bool:
        if not cls._filename_matches_uri(body_part, uri):
            return False
        body_part_category = cls._get_body_part_category(body_part)
        if cls._is_expected_content_body_part(category, body_part_category):
            return True
        metadata_category = cls._get_body_part_metadata_category(category)
        return cls._is_expected_metadata_body_part(
            metadata_category,
            body_part_category,
        )

    @staticmethod
    def _filename_matches_uri(
        body_part: DocumentsBodyPart,
        uri: str,
    ) -> bool:
        return body_part.content_disposition.filename == uri

    @staticmethod
    def _get_body_part_category(
        body_part: DocumentsBodyPart,
    ) -> list[str]:
        body_part_category = body_part.content_disposition.category or Category.CONTENT
        if isinstance(body_part_category, Category):
            body_part_category = [body_part_category]
        return [c.value for c in body_part_category]

    @staticmethod
    def _get_body_part_metadata_category(
        category: list[str],
    ) -> list[str]:
        metadata_category = list(category)
        if "content" in metadata_category:
            metadata_category.remove("content")
        return metadata_category

    @staticmethod
    def _is_expected_content_body_part(
        category: list[str],
        body_part_category: list[str],
    ) -> bool:
        return "content" in category and "content" in body_part_category

    @staticmethod
    def _is_expected_metadata_body_part(
        metadata_category: list[str],
        body_part_category: list[str],
    ) -> bool:
        if len(metadata_category) != len(body_part_category):
            return False
        return sorted(metadata_category) == sorted(body_part_category)

    @classmethod
    def _build_doc_objects(
        cls,
        body_parts: tuple[BodyPart],
    ) -> list[dict]:
        doc_objects = []
        for body_part in body_parts:
            content_disp = cls._get_content_disposition(body_part)
            if content_disp.body_part_type == DocumentsBodyPartType.ATTACHMENT:
                doc_object = cls._build_doc_object(doc_objects, body_part)
                doc_objects.append(doc_object)
        return doc_objects

    @classmethod
    def _build_doc_object(
        cls,
        doc_objects: list[dict],
        body_part: BodyPart,
    ) -> dict:
        content_disp = cls._get_content_disposition(body_part)
        uri = content_disp.filename
        existing_doc_object = cls._pop_object_with_uri(doc_objects, uri)

        if content_disp.category in [None, Category.CONTENT]:
            mime_type = cls._get_header_str(body_part, b"Content-Type")
            category = ["metadata", "content"]
        elif existing_doc_object:
            mime_type = existing_doc_object.get("mime-type")
            category = ["metadata", "content"]
        else:
            mime_type = ""
            category = ["metadata"]
        return {
            "uri": uri,
            "mime-type": mime_type,
            "category": category,
        }

    @classmethod
    def _get_content_disposition(
        cls,
        body_part: BodyPart,
    ) -> DocumentsContentDisposition:
        return ContentDispositionSerializer.serialize(
            cls._get_header_str(body_part, b"Content-Disposition"),
        )

    @staticmethod
    def _get_header_str(
        body_part: BodyPart,
        header: bytes,
    ) -> str:
        return body_part.headers.get(header).decode("utf-8")

    @staticmethod
    def _pop_object_with_uri(
        items: list[dict],
        uri: str,
    ) -> dict | None:
        for i, item in enumerate(items):
            if item.get("uri") == uri:
                return items.pop(i)
        return None

    @staticmethod
    def _build_no_document_error_get_response(
        uri: str,
    ) -> Response:
        code = httpx.codes.INTERNAL_SERVER_ERROR
        content = {
            "errorResponse": {
                "statusCode": code,
                "status": "Internal Server Error",
                "messageCode": "RESTAPI-NODOCUMENT",
                "message": "RESTAPI-NODOCUMENT: (err:FOER0000) "
                "Resource or document does not exist:  "
                f"category: content message: {uri}",
            },
        }
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        return Response(status_code=code, headers=headers, json=content)

    @classmethod
    def _build_doc_not_found_error_post_response(
        cls,
        uri: str,
        body_part: BodyPart,
    ) -> Response:
        code = httpx.codes.INTERNAL_SERVER_ERROR
        operation = cls._get_post_erroneous_operation(uri, body_part)
        content = {
            "errorResponse": {
                "statusCode": code,
                "status": "Internal Server Error",
                "messageCode": "XDMP-DOCNOTFOUND",
                "message": f"XDMP-DOCNOTFOUND: {operation} -- Document not found",
            },
        }
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        return Response(status_code=code, headers=headers, json=content)

    @staticmethod
    def _build_successful_single_part_get_response(
        body_part: DocumentsBodyPart,
    ) -> Response:
        content_type = f"{body_part.content_type}; charset=utf-8"
        doc_format = body_part.content_disposition.format_.value
        headers = {
            "Content-Type": content_type,
            "vnd.marklogic.document-format": doc_format,
        }
        return Response(
            status_code=httpx.codes.OK,
            headers=headers,
            content=body_part.content,
        )

    @staticmethod
    def _build_successful_multipart_get_response(
        form_data_fields: list[RequestField],
    ) -> Response:
        content, content_type = urllib3.encode_multipart_formdata(
            form_data_fields,
        )
        content_type = content_type.replace(
            "multipart/form-data",
            "multipart/mixed",
        )
        headers = {
            "Content-Type": content_type,
        }
        if len(form_data_fields) == 0:
            content = b""
            headers["Content-Length"] = "0"
        return Response(status_code=httpx.codes.OK, headers=headers, content=content)

    @staticmethod
    def _build_successful_post_response(
        doc_objects: list[dict],
    ) -> Response:
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "vnd.marklogic.document-format": "json",
        }
        content = {"documents": doc_objects}
        return Response(status_code=httpx.codes.OK, headers=headers, json=content)

    @staticmethod
    def _get_post_erroneous_operation(
        uri: str,
        body_part: BodyPart,
    ) -> str:
        metadata = json.loads(body_part.content.decode("utf-8"))
        if metadata.get("collections") and len(metadata.get("collections")) > 0:
            collections = metadata.get("collections")
            if len(collections) == 1:
                col_str = f'"{collections[0]}"'
            else:
                col_str = "(" + ", ".join(f'"{c}"' for c in collections) + ")"
            return f'xdmp:document-set-collections("{uri}", {col_str})'
        raise NotImplementedError
