from __future__ import annotations

import json
from abc import ABCMeta, abstractmethod
from typing import Any, Callable, List, Optional, Union

import respx
import urllib3
from httpx import Headers, Request, Response
from pydantic import BaseModel, ConfigDict
from respx import MockRouter
from urllib3.fields import RequestField

from mlclient.constants import HEADER_X_WWW_FORM_URLENCODED
from mlclient.structures.calls import (
    Category,
    ContentDispositionSerializer,
    DocumentsBodyPart,
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


class RespXRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: Optional[str] = None
    url: str = ""
    method: str = ""
    params: Optional[List[tuple]] = None
    headers: Optional[Headers] = None
    content: Optional[Union[bytes, str]] = None
    data: Optional[dict] = None
    json: Optional[dict] = None


class RespXResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    status_code: int = -1
    headers: Optional[Headers] = None
    content: Optional[Union[bytes, str]] = None
    json: Optional[dict] = None
    body_parts: Optional[list[RequestField]] = None


class RespXMock(BaseModel):
    request: RespXRequest = RespXRequest()
    response: RespXResponse = RespXResponse()
    side_effect: Optional[Callable] = None


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
            self._resp_mock.request.json = body
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
            self._resp_mock.response.json = body
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

    def with_side_effect(self, side_effect: Callable):
        self._resp_mock.side_effect = side_effect

    def mock_response(
        self,
    ):
        if self._resp_mock.side_effect:
            self._mock.request(
                **self._resp_mock.request.model_dump(exclude_none=True),
            ).mock(side_effect=self._resp_mock.side_effect)
        else:
            self._validate()
            self._setup_response_body()
            self._mock.request(
                **self._resp_mock.request.model_dump(exclude_none=True),
            ).respond(
                **self._resp_mock.response.model_dump(
                    exclude={"body_parts"},
                    exclude_none=True,
                ),
            )
        self._resp_mock = RespXMock()

    def _validate(self):
        bodies = [
            body
            for body in [
                self._resp_mock.response.content,
                self._resp_mock.response.json,
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
    def __init__(self, document_body_parts: list[DocumentsBodyPart]):
        self._doc_body_parts = list(document_body_parts)

    def get_documents_side_effect(
        self,
        request: Request,
    ):
        uris = request.url.params.get_list("uri")
        category = request.url.params.get_list("category")
        if len(category) == 0:
            category = ["content"]
        return self.get_documents(uris, category)

    def get_documents(
        self,
        uris: list[str],
        category: list[str],
    ) -> Response:
        if len(uris) == 1 and len(category) == 1:
            return self._for_single_uri(uris[0], category)
        return self._for_multiple_uris(uris, category)

    def _for_single_uri(
        self,
        uri: str,
        category: list[str],
    ) -> Response:
        body_parts = self._find_body_parts(uri, category)
        if len(body_parts) == 0:
            code = 500
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
            return Response(status_code=code, json=content)

        body_part = body_parts[0]
        content_type = f"{body_part.content_type}; charset=utf-8"
        content = body_part.content
        doc_format = body_part.content_disposition.format_.value
        headers = {
            "Content-Type": content_type,
            "vnd.marklogic.document-format": doc_format,
        }
        return Response(status_code=200, headers=headers, content=content)

    def _for_multiple_uris(
        self,
        uris: list,
        category: list[str],
    ) -> Response:
        response_body_fields = []
        for uri in uris:
            for body_part in self._find_body_parts(uri, category):
                if body_part is None:
                    continue
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
                response_body_fields.append(req_field)
        content, content_type = urllib3.encode_multipart_formdata(
            response_body_fields,
        )
        content_type = content_type.replace(
            "multipart/form-data",
            "multipart/mixed",
        )
        headers = {
            "Content-Type": content_type,
        }
        if len(response_body_fields) == 0:
            content = b""
            headers["Content-Length"] = "0"
        return Response(status_code=200, headers=headers, content=content)

    def _find_body_parts(
        self,
        uri: str,
        category: list[str],
    ) -> list[DocumentsBodyPart] | None:
        return [
            part
            for part in self._doc_body_parts
            if self._match_body_part(uri, category, part)
        ]

    @staticmethod
    def _match_body_part(
        uri: str,
        category: list[str],
        body_part: DocumentsBodyPart,
    ) -> bool:
        if body_part.content_disposition.filename != uri:
            return False
        body_part_category = body_part.content_disposition.category or Category.CONTENT
        if isinstance(body_part_category, Category):
            body_part_category = [body_part_category]
        body_part_category = [c.value for c in body_part_category]
        if "content" in category and "content" in body_part_category:
            return True
        metadata_categories = list(category)
        if "content" in metadata_categories:
            metadata_categories.remove("content")
        if len(metadata_categories) != len(body_part_category):
            return False
        return sorted(metadata_categories) == sorted(body_part_category)
