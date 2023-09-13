from __future__ import annotations

import os
import urllib.parse
from pathlib import Path
from typing import Any, Iterable

import responses
from requests import Response
from requests_toolbelt import MultipartEncoder, MultipartDecoder
from responses import matchers

_SCRIPT_DIR = Path(__file__).resolve()
_RESOURCES_DIR = "resources"
_COMMON_RESOURCES_DIR = "common"
TESTS_PATH = Path(_SCRIPT_DIR).parent
RESOURCES_PATH = next(TESTS_PATH.glob(_RESOURCES_DIR))
COMMON_RESOURCES_PATH = next(RESOURCES_PATH.glob(_COMMON_RESOURCES_DIR))


def list_resources(
        test_path: str,
) -> list[str]:
    test_resources_path = get_test_resources_path(test_path)
    return os.listdir(test_resources_path)


def get_test_resource_path(
        test_path: str,
        resource: str,
) -> str:
    test_resources_path = get_test_resources_path(test_path)
    return next(Path(test_resources_path).glob(resource)).as_posix()


def get_common_resource_path(
        resource: str,
) -> str:
    return next(COMMON_RESOURCES_PATH.glob(resource)).as_posix()


def get_test_resources_path(
        test_path: str,
) -> str:
    tests_path = TESTS_PATH.as_posix()
    resources_rel_path = test_path.replace(tests_path, "")[1:-3]
    resources_rel_path = resources_rel_path.replace("_", "-")
    return next(Path(RESOURCES_PATH).glob(resources_rel_path)).as_posix()


class MLResponseBuilder:

    def __init__(
            self,
    ):
        self._method: str | None = None
        self._base_url: str | None = None
        self._response_body: str | bytes | None = None
        self._response_body_fields: dict | None = None
        self._response_status: int | None = None
        self._request_body: str | None = None
        self._params: dict = {}
        self._headers: dict = {}
        self._content_type: str | None = None

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

    def with_empty_response_body(
            self,
    ):
        self.with_response_body(b"")
        self.with_header("Content-Length", 0)

    def with_response_body(
            self,
            body,
    ):
        self._response_body = body

    def with_response_body_part(
            self,
            x_primitive: str,
            body_part_content: Any,
    ):
        if not self._response_body_fields:
            self._response_body_fields = {}

        index = len(self._response_body_fields) + 1
        name_disposition = f"name{index}"
        field_name = f"field{index}"

        if x_primitive in ["array", "map"]:
            content_type = "application/json"
        elif x_primitive in ["document", "element"]:
            content_type = "application/xml"
        else:
            content_type = "text/plain"

        headers = {"X-Primitive": x_primitive}
        self._response_body_fields[field_name] = (
            name_disposition, body_part_content, content_type, headers,
        )

    def with_response_status(
            self,
            status: int,
    ):
        self._response_status = status

    def with_request_body(
            self,
            body: Any,
    ):
        self._request_body = body

    def with_params(
            self,
            params: dict,
    ):
        for key, value in params.items():
            self.with_param(key, value)

    def with_param(
            self,
            key: str,
            value: Any,
    ):
        self._params[key] = value

    def with_header(
            self,
            key: str,
            value: Any,
    ):
        self._headers[key] = str(value)

    def build_get(
            self,
    ):
        self.with_method("GET")
        self.build()

    def build_post(
            self,
    ):
        self.with_method("POST")
        self.build()

    def build(
            self,
    ):
        self._validate()
        request_url, responses_params = self._build()
        self._finalize(request_url, responses_params)
        self.__init__()

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
        if len(self._params) > 0:
            params = urllib.parse.urlencode(self._params).replace("%2B", "+")
            request_url += f"?{params}"
        return request_url

    def _build_responses_params(
            self,
    ):
        responses_params = {}

        if self._response_status:
            responses_params["status"] = self._response_status

        if self._response_body is not None:
            body_param = "json" if isinstance(self._response_body, dict) else "body"
            responses_params[body_param] = self._response_body
            responses_params["headers"] = self._headers
        elif self._response_body_fields is not None:
            multipart_body = MultipartEncoder(fields=self._response_body_fields)
            multipart_body_str = multipart_body.to_string()
            boundary = multipart_body.boundary[2:]
            content_type = f"multipart/mixed; boundary={boundary}"
            self.with_header("Content-Length", len(multipart_body_str))

            responses_params["body"] = multipart_body_str
            responses_params["content_type"] = content_type
            responses_params["headers"] = self._headers

        return responses_params

    def _finalize(
            self,
            request_url: str,
            responses_params: dict,
    ):
        if self._method == "GET":
            self._finalize_get(request_url, responses_params)
        elif self._method == "POST":
            self._finalize_post(request_url, self._request_body, responses_params)

    @staticmethod
    def _finalize_get(
            request_url: str,
            responses_params: dict,
    ):
        responses.get(
            request_url,
            **responses_params,
        )

    @staticmethod
    def _finalize_post(
            request_url: str,
            request_body: Any,
            responses_params: dict,
    ):
        match = [matchers.urlencoded_params_matcher(request_body)]
        responses_params["match"] = match
        responses.post(
            request_url,
            **responses_params,
        )

    @staticmethod
    def error_logs_body(
            logs: list[tuple],
    ):
        return {
            "logfile": {
                "log": [
                    {
                        "timestamp": log_tuple[0],
                        "level": log_tuple[1],
                        "message": log_tuple[2],
                    }
                    for log_tuple in logs
                ],
            },
        }

    @staticmethod
    def access_or_request_logs_body(
            logs: list[str],
    ):
        return {
            "logfile": {
                "message": "\n".join(logs),
            },
        }

    @staticmethod
    def generate_builder_code(
            origin_response: Response,
    ):
        init = "\nbuilder = MLResponseBuilder()"
        method = f'builder.with_method("{origin_response.request.method.upper()}")'
        url_split = urllib.parse.urlsplit(origin_response.url)
        url = f"{url_split.scheme}://{url_split.netloc}{url_split.path}"
        base_url = f'builder.with_base_url("{url}")'
        joined_params = url_split.query
        if joined_params == "":
            params = None
        else:
            params = [f'builder.with_param("{param.split("=")[0]}", "{param.split("=")[1]}")'
                      for param in joined_params.split("&")]
        if origin_response.request.method.upper() in ["POST", "PUT"]:
            if origin_response.request.headers.get("Content-Type") == "application/x-www-form-urlencoded":
                origin_body = urllib.parse.unquote(origin_response.request.body).replace("+", " ")
                split = origin_body.split("&")
                body = {}
                for part in split:
                    key_and_value = part.split("=")
                    body[key_and_value[0]] = key_and_value[1]
                request_body = f'builder.with_request_body({body})'
            else:
                request_body = f'builder.with_request_body(\'{origin_response.request.body}\')'
        else:
            request_body = None
        headers = [f'builder.with_header("{name}", "{value}")'
                   for name, value in origin_response.headers.items()
                   if name not in ["Content-Length", "Content-Type"]]
        status = f"builder.with_response_status({origin_response.status_code})"
        if origin_response.content == b"":
            response_body = f'builder.with_empty_response_body()'
        else:
            if origin_response.headers.get("Content-Type").startswith("multipart/mixed"):
                raw_parts = MultipartDecoder.from_response(origin_response).parts
                response_body = []
                for part in raw_parts:
                    encoded_header_name = "X-Primitive".encode(part.encoding)
                    header_value = part.headers.get(encoded_header_name)
                    x_primitive = header_value.decode(part.encoding)
                    body_part_content = part.text
                    response_body.append(f'builder.with_response_body_part("{x_primitive}", "{body_part_content}")')
            else:
                body = origin_response.text.replace("'", "\\'")
                response_body = f'builder.with_response_body(\'\'\'{body}\'\'\')'
        build = "builder.build()"
        code_lines = [
            init,
            method,
            base_url,
            params,
            request_body,
            headers,
            status,
            response_body,
            build,
        ]
        for code_line in code_lines:
            if code_line is not None:
                if isinstance(code_line, list):
                    for line in code_line:
                        print(line)
                else:
                    print(code_line)
