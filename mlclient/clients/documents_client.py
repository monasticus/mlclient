from __future__ import annotations

from typing import Iterator

from requests import Response

from mlclient import constants
from mlclient.calls import DocumentsGetCall
from mlclient.calls.model import Category, DocumentsContentDisposition
from mlclient.clients import MLResourceClient, MLResponseParser
from mlclient.exceptions import MarkLogicError
from mlclient.model import (Document, DocumentFactory, Metadata,
                            MetadataDocument)


class DocumentsClient(MLResourceClient):

    def read(
            self,
            uri: str | list[str] | tuple[str] | set[str],
            category: str | list | None = None,
    ) -> Document | list[Document]:
        call = self._get_call(uri=uri, category=category)
        resp = self.call(call)
        parsed_resp_with_headers = self._parse_response(resp)
        documents_data = self._pre_format_data(parsed_resp_with_headers, uri, category)
        docs = self._parse_to_documents(documents_data)
        if len(docs) == 1:
            docs = docs[0]
        return docs

    @classmethod
    def _get_call(
            cls,
            uri: str | list[str] | tuple[str] | set[str],
            category: str | list | None,
    ) -> DocumentsGetCall:
        params = {
            "uri": uri,
            "category": category,
        }
        if category and category != "content" or isinstance(category, list):
            params["data_format"] = "json"

        return DocumentsGetCall(**params)

    @classmethod
    def _parse_response(
            cls,
            resp: Response,
    ) -> list[tuple]:
        if not resp.ok:
            resp_body = resp.json()
            raise MarkLogicError(resp_body["errorResponse"])
        parsed_resp_with_headers = MLResponseParser.parse_with_headers(resp)
        if isinstance(parsed_resp_with_headers, tuple):
            return [parsed_resp_with_headers]
        return parsed_resp_with_headers

    @classmethod
    def _pre_format_data(
            cls,
            parsed_resp_with_headers: list[tuple],
            origin_uri: str | list[str] | tuple[str] | set[str],
            origin_category: str | list | None,
    ) -> Iterator[dict]:
        if len(parsed_resp_with_headers) == 1:
            headers, parsed_resp = parsed_resp_with_headers[0]
            is_multipart = any(header.lower() == "content-disposition"
                               for header in headers)
            if is_multipart:
                content_disp = cls._get_content_disposition(headers)
                uri = content_disp.filename
                category = content_disp.category
                if category == Category.CONTENT:
                    category_key = "content"
                    doc_format = content_disp.format_
                else:
                    category_key = "metadata"
                    doc_format = None
                data = {
                    "uri": uri,
                    "format": doc_format,
                    category_key: parsed_resp,
                }
            else:
                if not origin_category or Category.CONTENT.value in origin_category:
                    category_key = "content"
                    doc_format = headers.get(constants.HEADER_NAME_ML_DOCUMENT_FORMAT)
                else:
                    category_key = "metadata"
                    doc_format = None
                uri = origin_uri[0] if isinstance(origin_uri, list) else origin_uri
                data = {
                    "uri": uri,
                    "format": doc_format,
                    category_key: parsed_resp,
                }
            yield data
        else:
            uris = {cls._get_content_disposition(headers).filename
                    for headers, _ in parsed_resp_with_headers}
            for uri in uris:
                yield cls._pre_formatted_data(parsed_resp_with_headers, uri)

    @classmethod
    def _pre_formatted_data(
            cls,
            parsed_resp_with_headers: list[tuple],
            uri: str,
    ) -> dict:
        content_part = next(
            cls._find_part_by_uri_and_condition(
                parsed_resp_with_headers,
                uri,
                lambda cat: cat == Category.CONTENT,
            ), None)
        metadata_part = next(
            cls._find_part_by_uri_and_condition(
                parsed_resp_with_headers,
                uri,
                lambda cat: cat != Category.CONTENT,
            ), None)

        data = {"uri": uri}
        if content_part:
            headers, parsed_resp = content_part
            content_disp = cls._get_content_disposition(headers)
            data["format"] = content_disp.format_
            data["content"] = parsed_resp
        if metadata_part:
            headers, parsed_resp = metadata_part
            data["metadata"] = parsed_resp
        return data

    @classmethod
    def _find_part_by_uri_and_condition(
            cls,
            parsed_resp_with_headers: list[tuple],
            uri: str,
            category_condition,
    ) -> Iterator[tuple]:
        for headers, parsed_resp in parsed_resp_with_headers:
            content_disp = cls._get_content_disposition(headers)
            if (content_disp.filename == uri and
                    category_condition(content_disp.category)):
                yield headers, parsed_resp

    @classmethod
    def _get_content_disposition(
            cls,
            headers: dict,
    ) -> DocumentsContentDisposition:
        content_disp = headers.get(constants.HEADER_NAME_CONTENT_DISP).split("; ")
        disp_dict = {}
        for disp in content_disp:
            key_value_pair = disp.split("=")
            if len(key_value_pair) == 1:
                disp_dict["body_part_type"] = key_value_pair[0]
            else:
                key = key_value_pair[0]
                value = key_value_pair[1]
                if key == "filename":
                    value = value[1:-1]
                curr_value = disp_dict.get(key)
                if curr_value is None:
                    disp_dict[key] = value
                elif not isinstance(curr_value, list):
                    disp_dict[key] = [curr_value, value]
                else:
                    curr_value.append(value)
        return DocumentsContentDisposition(**disp_dict)

    @classmethod
    def _parse_to_documents(
            cls,
            documents_data: Iterator[dict],
    ) -> list[Document]:
        return [cls._parse_to_document(document_data)
                for document_data in documents_data]

    @classmethod
    def _parse_to_document(
            cls,
            document_data: dict,
    ) -> Document:
        uri = document_data.get("uri")
        doc_format = document_data.get("format")
        content_raw = document_data.get("content")
        metadata_raw = document_data.get("metadata")
        metadata = cls._parse_metadata(metadata_raw)
        if content_raw:
            return DocumentFactory.build_document(content=content_raw,
                                                  doc_type=doc_format,
                                                  uri=uri,
                                                  metadata=metadata)
        return MetadataDocument(uri=uri,
                                metadata=metadata)

    @classmethod
    def _parse_metadata(
            cls,
            metadata_raw: dict | None,
    ) -> Metadata | None:
        if not metadata_raw:
            return None

        if "metadataValues" in metadata_raw:
            metadata_raw["metadata_values"] = metadata_raw["metadataValues"]
            del metadata_raw["metadataValues"]

        return Metadata(**metadata_raw)
