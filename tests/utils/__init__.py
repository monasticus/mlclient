from __future__ import annotations

import functools
import inspect
import json
import operator
import os
import urllib.parse
import zlib
from pathlib import Path
from typing import Any

import responses
import urllib3
from requests import Response
from requests_toolbelt import MultipartDecoder
from requests_toolbelt.multipart.decoder import BodyPart
from responses import matchers
from urllib3.fields import RequestField

from mlclient.structures.calls import ContentDispositionSerializer, DocumentsBodyPart
from mlclient.constants import (
    HEADER_JSON,
    HEADER_MULTIPART_MIXED,
    HEADER_NAME_CONTENT_DISP,
    HEADER_NAME_CONTENT_TYPE,
    HEADER_NAME_PRIMITIVE,
    HEADER_X_WWW_FORM_URLENCODED,
)
from tests.utils import resources as resources_utils


class MLResponseBuilder:
    def __init__(
        self,
    ):
        self._method: str | None = None
        self._base_url: str | None = None
        self._request_body: str | None = None
        self._request_params: list[tuple] = []
        self._request_content_type: str | None = None
        self._multipart_mixed_response: bool = False
        self._response_body: str | bytes | None = None
        self._response_body_fields: list | None = None
        self._response_status: int | None = None
        self._response_headers: dict = {}

    def with_method(
        self,
        method: str,
    ):
        self._method = method

    def with_base_url(
        self,
        base_url: str,
    ):
        self._base_url = base_url

    def with_request_body(
        self,
        body: Any,
    ):
        self._request_body = body

    def with_request_params(
        self,
        params: dict,
    ):
        for key, value in params.items():
            self.with_request_param(key, value)

    def with_request_param(
        self,
        key: str,
        value: Any,
    ):
        self._request_params.append((key, value))

    def with_request_content_type(
        self,
        content_type: str,
    ):
        self._request_content_type = content_type

    def with_response_body_multipart_mixed(
        self,
    ):
        self._multipart_mixed_response = True

    def with_empty_response_body(
        self,
    ):
        self.with_response_body(b"")
        self.with_response_header("Content-Length", 0)

    def with_response_body(
        self,
        body,
    ):
        if self._multipart_mixed_response and body != b"":
            func = "MLResponseBuilder.with_response_body_part()"
            msg = f"multipart/mixed response set to True: use {func} instead"
            raise RuntimeError(msg)
        self._response_body = body

    def with_response_body_part(
        self,
        x_primitive: str | None,
        body_part_content: Any,
        content_type: str | None = None,
    ):
        if not self._multipart_mixed_response:
            func = "MLResponseBuilder.with_response_body_multipart_mixed()"
            msg = f"multipart/mixed response set to False: use {func} first"
            raise RuntimeError(msg)

        if not self._response_body_fields:
            self._response_body_fields = []

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
        self._response_body_fields.append(req_field)

    def with_response_documents_body_part(
        self,
        body_part: DocumentsBodyPart,
    ):
        if not self._multipart_mixed_response:
            func = "MLResponseBuilder.with_response_body_multipart_mixed()"
            msg = f"multipart/mixed response set to False: use {func} first"
            raise RuntimeError(msg)

        if not self._response_body_fields:
            self._response_body_fields = []

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
        self._response_body_fields.append(req_field)

    def with_response_status(
        self,
        status: int,
    ):
        self._response_status = status

    def with_response_content_type(
        self,
        content_type: str,
    ):
        self.with_response_header("Content-Type", content_type)

    def with_response_header(
        self,
        key: str,
        value: Any,
    ):
        self._response_headers[key] = str(value)

    def build_get(
        self,
    ):
        self.with_method("GET")
        return self.build()

    def build_delete(
        self,
    ):
        self.with_method("DELETE")
        return self.build()

    def build_post(
        self,
    ):
        self.with_method("POST")
        return self.build()

    def build_put(
        self,
    ):
        self.with_method("PUT")
        return self.build()

    def build(
        self,
    ):
        self._validate()
        request_url, responses_params = self._build()
        resp_obj = self._finalize(request_url, responses_params)
        self.__init__()
        return resp_obj

    def _validate(
        self,
    ):
        if self._response_body and self._response_body_fields:
            msg = "You can't set a regular and multipart response bodies!"
            raise RuntimeError(msg)

    def _build(
        self,
    ):
        request_url = self._build_request_url()
        responses_params = self._build_responses_params()
        return request_url, responses_params

    def _build_request_url(
        self,
    ):
        request_url = self._base_url
        if len(self._request_params) > 0:
            params = urllib.parse.urlencode(self._request_params).replace("%2B", "+")
            request_url += f"?{params}"
        return request_url

    def _build_responses_params(
        self,
    ):
        responses_params = {}

        if self._response_status:
            responses_params["status"] = self._response_status

        if not self._multipart_mixed_response:
            if isinstance(self._response_body, dict):
                body_param = "json"
                length = len(json.dumps(self._response_body))
            else:
                body_param = "body"
                length = len(self._response_body)
            self.with_response_header("Content-Length", length)
            responses_params[body_param] = self._response_body
            if "Content-Type" in self._response_headers:
                content_type = self._response_headers["Content-Type"]
                responses_params["content_type"] = content_type
                del self._response_headers["Content-Type"]
            responses_params["headers"] = self._response_headers
        else:
            body, content_type = urllib3.encode_multipart_formdata(
                self._response_body_fields or [],
            )
            if self._response_body == b"":
                body = self._response_body
            content_type = content_type.replace(
                "multipart/form-data",
                "multipart/mixed",
            )
            self.with_response_header("Content-Length", len(body))

            responses_params["body"] = body
            responses_params["content_type"] = content_type
            responses_params["headers"] = self._response_headers

        return responses_params

    def _finalize(
        self,
        request_url: str,
        responses_params: dict,
    ):
        if self._method == "GET":
            return self._finalize_get(request_url, responses_params)
        if self._method == "DELETE":
            return self._finalize_delete(request_url, responses_params)
        if self._method == "POST":
            return self._finalize_post(
                request_url,
                responses_params,
                self._request_content_type,
                self._request_body,
            )
        if self._method == "PUT":
            return self._finalize_put(
                request_url,
                responses_params,
                self._request_content_type,
                self._request_body,
            )
        msg = "MLResponseBuilder - supported methods are: GET, DELETE, POST, PUT"
        raise RuntimeError(msg)

    @staticmethod
    def _finalize_get(
        request_url: str,
        responses_params: dict,
    ):
        return responses.get(
            request_url,
            **responses_params,
        )

    @staticmethod
    def _finalize_delete(
        request_url: str,
        responses_params: dict,
    ):
        return responses.delete(
            request_url,
            **responses_params,
        )

    @staticmethod
    def _finalize_post(
        request_url: str,
        responses_params: dict,
        request_content_type: str | None,
        request_body: Any,
    ):
        if request_content_type:
            if request_content_type.startswith("application/x-www-form-urlencoded"):
                match = [matchers.urlencoded_params_matcher(request_body)]
                responses_params["match"] = match
            elif request_content_type.startswith("application/json"):
                match = [matchers.json_params_matcher(request_body)]
                responses_params["match"] = match
        return responses.post(
            request_url,
            **responses_params,
        )

    @staticmethod
    def _finalize_put(
        request_url: str,
        responses_params: dict,
        request_content_type: str,
        request_body: Any,
    ):
        if request_content_type:
            if request_content_type.startswith("application/x-www-form-urlencoded"):
                match = [matchers.urlencoded_params_matcher(request_body)]
                responses_params["match"] = match
            elif request_content_type.startswith("application/json"):
                match = [matchers.json_params_matcher(request_body)]
                responses_params["match"] = match
        return responses.put(
            request_url,
            **responses_params,
        )

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

    @staticmethod
    def logs_list_body(
        items: list[dict],
    ) -> dict:
        return {
            "log-default-list": {
                "list-items": {
                    "list-item": items,
                },
            },
        }

    @classmethod
    def generate_builder_code(
        cls,
        response: Response,
        save_response_body: bool = False,
        test_path: str | None = None,
    ):
        build_parts = [
            "\n",
            "builder = MLResponseBuilder()",
            cls._generate_base_url_line(response),
            cls._generate_request_content_type_line(response),
            cls._generate_request_params_lines(response),
            cls._generate_request_body_lines(response),
            cls._generate_response_headers_lines(response),
            cls._generate_response_status_line(response),
            cls._generate_response_body_lines(response, save_response_body, test_path),
            cls._generate_build_line(response),
            "\n",
        ]
        build_parts = cls._flatten_list(build_parts)
        cls._move_resp_body_path_line_to_front(build_parts)
        for code in build_parts:
            if code is not None:
                print(code)

    @classmethod
    def _generate_base_url_line(
        cls,
        response: Response,
    ) -> str:
        url = response.url
        url_split = urllib.parse.urlsplit(url)
        base_url = f"{url_split.scheme}://{url_split.netloc}{url_split.path}"
        return f'builder.with_base_url("{base_url}")'

    @classmethod
    def _generate_request_params_lines(
        cls,
        response: Response,
    ) -> list[str] | None:
        url = response.url
        url_split = urllib.parse.urlsplit(url)
        url_query = urllib.parse.unquote(url_split.query)
        if url_query == "":
            return None

        params_lines = []
        for param in url_query.split("&"):
            name_and_value = param.split("=")
            param_name = name_and_value[0]
            param_value = name_and_value[1]
            param_line = f'builder.with_request_param("{param_name}", "{param_value}")'
            params_lines.append(param_line)
        return params_lines

    @classmethod
    def _generate_request_content_type_line(
        cls,
        response: Response,
    ) -> str | None:
        content_type = response.request.headers.get("content-type")
        if not content_type:
            return None
        return f'builder.with_request_content_type("{content_type}")'

    @classmethod
    def _generate_request_body_lines(
        cls,
        response: Response,
    ) -> str | None:
        method = response.request.method.upper()
        request_content_type = response.request.headers.get("Content-Type")
        request_body = response.request.body

        if request_body is None or method not in ["POST", "PUT"]:
            return None

        if request_content_type.startswith(HEADER_JSON):
            request_body = json.loads(request_body)

        if request_content_type != HEADER_X_WWW_FORM_URLENCODED:
            if isinstance(request_body, str):
                return f"builder.with_request_body('{request_body}')"
            return f"builder.with_request_body({request_body})"

        request_body_decoded = urllib.parse.unquote(request_body).replace("+", " ")
        request_body_parts = request_body_decoded.split("&")
        body = {}
        for part in request_body_parts:
            key_and_value = part.split("=")
            part_name = key_and_value[0]
            part_value = "=".join(key_and_value[1:])
            body[part_name] = part_value
        return f"builder.with_request_body({body})"

    @classmethod
    def _generate_response_headers_lines(
        cls,
        response: Response,
    ) -> list[str]:
        response_headers = response.headers
        response_content_type = response_headers.get("Content-Type")
        excluded = ["Content-Length", "Content-Type"]
        if "Content-Type" in response_headers and "Content-type" in response_headers:
            excluded.append("Content-type")

        response_headers_lines = []
        if response_content_type is not None:
            if not response_content_type.startswith(HEADER_MULTIPART_MIXED):
                content_type_line = (
                    f'builder.with_response_content_type("{response_content_type}")'
                )
            else:
                content_type_line = "builder.with_response_body_multipart_mixed()"
            response_headers_lines.append(content_type_line)

        for name, value in response_headers.items():
            if name not in excluded:
                header_line = f'builder.with_response_header("{name}", "{value}")'
                response_headers_lines.append(header_line)

        return response_headers_lines

    @classmethod
    def _generate_response_status_line(
        cls,
        response: Response,
    ) -> str:
        status_code = response.status_code
        return f"builder.with_response_status({status_code})"

    @classmethod
    def _generate_response_body_lines(
        cls,
        response: Response,
        save_response_body: bool,
        test_path: str | None,
    ) -> list[str]:
        if not save_response_body:
            return cls._generate_response_body_raw_lines(response)

        return cls._generate_response_body_file_lines(response, test_path)

    @classmethod
    def _generate_response_body_raw_lines(
        cls,
        response: Response,
    ):
        response_content_type = response.headers.get("content-type")
        response_body_text = response.text

        if response.content == b"":
            return ["builder.with_empty_response_body()"]

        if not response_content_type.startswith(HEADER_MULTIPART_MIXED):
            body = response_body_text.replace("'", "\\'")

            if response_content_type.startswith(HEADER_JSON):
                return [f"builder.with_response_body({body})"]
            if "\n" in body:
                return [f"builder.with_response_body('''{body}''')"]

            return [f"builder.with_response_body('{body}')"]

        response_body_lines = []
        raw_parts = MultipartDecoder.from_response(response).parts
        for part in raw_parts:
            x_primitive = cls._decode_header(part, HEADER_NAME_PRIMITIVE)
            content_type = cls._decode_header(part, HEADER_NAME_CONTENT_TYPE)
            content_disp = cls._decode_header(part, HEADER_NAME_CONTENT_DISP)

            if content_type != "application/zip":
                body_part_content = part.text.replace("'", "\\'")
            else:
                body_part_content = zlib.decompress(part.content)
                body_part_content = body_part_content.replace(b"'", b"\\'")

            if response.request.path_url.startswith("/v1/documents"):
                doc_body_part = {
                    "content-type": content_type,
                    "content-disposition": content_disp,
                    "content": body_part_content,
                }
                response_body_line = (
                    "builder.with_response_documents_body_part("
                    f"DocumentsBodyPart(**{doc_body_part}"
                    "))"
                )
            else:
                if isinstance(body_part_content, bytes):
                    ...
                elif "\n" in body_part_content:
                    body_part_content = f"'''{body_part_content}'''"
                else:
                    body_part_content = f"'{body_part_content}'"
                response_body_line = (
                    "builder.with_response_body_part("
                    f'"{x_primitive}", {body_part_content}'
                    ")"
                )
            response_body_lines.append(response_body_line)
        return response_body_lines

    @classmethod
    def _generate_build_line(
        cls,
        response: Response,
    ) -> str:
        method = response.request.method.lower()
        return f"builder.build_{method}()"

    @classmethod
    def _decode_header(
        cls,
        body_part: BodyPart,
        header_name: str,
    ) -> str | None:
        name_enc = header_name.encode(body_part.encoding)
        value_enc = body_part.headers.get(name_enc)
        if value_enc is None:
            return None
        return value_enc.decode(body_part.encoding)

    @classmethod
    def _generate_response_body_file_lines(
        cls,
        response: Response,
        test_path: str,
    ):
        response_content_type = response.headers.get("Content-Type")
        response_body_text = response.text

        ext = cls._get_file_ext_from_content_type(response_content_type)

        if test_path is None:
            file_name = f"response_body.{ext}"
            path = file_name
        else:
            file_name = inspect.stack()[3].function.replace("_", "-") + f".{ext}"
            path = (
                resources_utils.get_test_resources_path(test_path) + os.sep + file_name
            )

        with Path(path).open("w") as file:
            file.write(response_body_text)

        if test_path is None:
            return [f'builder.with_response_body(Path("{path}").read_bytes())']

        return [
            f"response_body_path = "
            f'resources_utils.get_test_resource_path(__file__, "{file_name}")',
            "builder.with_response_body(Path(response_body_path).read_bytes())",
        ]

    @staticmethod
    def _get_file_ext_from_content_type(
        content_type: str,
    ):
        if "html" in content_type:
            return "html"
        if "xml" in content_type:
            return "xml"
        if "json" in content_type:
            return "json"
        return "txt"

    @classmethod
    def _flatten_list(
        cls,
        build_parts: list,
    ) -> list:
        build_parts = [
            [elem] if not isinstance(elem, list) else elem for elem in build_parts
        ]
        return functools.reduce(operator.iconcat, build_parts, [])

    @classmethod
    def _move_resp_body_path_line_to_front(
        cls,
        build_parts: list,
    ):
        gen = (
            build_parts.index(line)
            for line in build_parts
            if isinstance(line, str) and line.startswith("response_body_path")
        )
        index = next(gen, None)
        if index:
            build_parts.insert(1, build_parts.pop(index))
