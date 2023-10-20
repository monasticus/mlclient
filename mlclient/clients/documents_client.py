from __future__ import annotations

import xml.etree.ElementTree as ElemTree
from typing import Iterator

from requests import Response

from mlclient import constants
from mlclient.calls import DocumentsGetCall
from mlclient.calls.model import DocumentsContentDisposition, Category
from mlclient.clients import MLResourceClient, MLResponseParser
from mlclient.exceptions import MarkLogicError
from mlclient.model import Document, DocumentFactory, Metadata


class DocumentsClient(MLResourceClient):

    def read(
            self,
            uri: str | list[str] | tuple[str] | set[str],
            category: str | list | None = None,
    ) -> Document | list[Document]:
        call = self._get_call(uri=uri, category=category)
        resp = self.call(call)
        parsed_resp_with_headers = self._parse_response(resp)
        data_groups = self._group_data_by_uri(parsed_resp_with_headers)
        docs = self._parse_to_documents(uri, data_groups)
        if len(docs) == 1:
            docs = docs[0]
        return docs

    @classmethod
    def _get_call(
            cls,
            uri: str | list[str] | tuple[str] | set[str],
            category: str | list | None,
    ):
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
    def _parse_to_documents(
            cls,
            uri: str | list[str] | tuple[str] | set[str],
            data_groups: Iterator[list[tuple]],
    ) -> list[Document]:
        return [cls._parse_to_document(uri, data_group)
                for data_group in data_groups]

    @classmethod
    def _parse_to_document(
            cls,
            uri: str | list[str] | tuple[str] | set[str],
            data_group: list[tuple],
    ) -> Document:
        is_multipart = any("content-disposition" == header.lower()
                           for headers, parsed_resp in data_group
                           for header in headers.keys())
        if is_multipart:
            content_part, metadata_parts = cls._split_data_group(data_group)
            content_headers, parsed_resp = content_part
            content_disp = cls._get_content_disposition(content_headers)
            uri = content_disp.filename[1:-1]
            doc_format = content_disp.format_
            metadata = cls._parse_metadata(metadata_parts)
            return DocumentFactory.build_document(content=parsed_resp,
                                                  doc_type=doc_format,
                                                  uri=uri,
                                                  metadata=metadata)
        else:
            headers, parsed_resp = data_group[0]
            uri = uri if isinstance(uri, str) else uri[0]
            doc_format = headers.get(constants.HEADER_NAME_ML_DOCUMENT_FORMAT)
            return DocumentFactory.build_document(content=parsed_resp,
                                                  doc_type=doc_format,
                                                  uri=uri)

    @classmethod
    def _get_content_disposition(
            cls,
            headers: dict,
    ) -> DocumentsContentDisposition:
        content_disp = headers.get(constants.HEADER_NAME_CONTENT_DISP).split("; ")
        disp_dict = {disp.split("=")[0]: disp.split("=")[1]
                     for disp in content_disp
                     if len(disp.split("=")) > 1}
        disp_dict["body_part_type"] = content_disp[0]
        return DocumentsContentDisposition(**disp_dict)

    @classmethod
    def _group_data_by_uri(
            cls,
            parsed_resp_with_headers: list[tuple],
    ) -> Iterator[list[tuple]]:
        if len(parsed_resp_with_headers) == 1:
            yield parsed_resp_with_headers
        else:
            uris = {cls._get_content_disposition(headers).filename
                    for headers, _ in parsed_resp_with_headers}
            for uri in uris:
                yield cls._data_referring_to_same_uri(parsed_resp_with_headers, uri)

    @classmethod
    def _data_referring_to_same_uri(
            cls,
            parsed_resp_with_headers: list[tuple],
            uri: str,
    ) -> list[tuple]:
        return [(headers, parsed_resp)
                for headers, parsed_resp in parsed_resp_with_headers
                if cls._get_content_disposition(headers).filename == uri]

    @classmethod
    def _split_data_group(
            cls,
            data_group: list[tuple],
    ) -> tuple[tuple | None, list[tuple] | None]:
        content_part = next(((headers, parsed_resp)
                             for headers, parsed_resp in data_group
                             if cls._get_content_disposition(headers).category == Category.CONTENT), None)
        metadata_parts = [(headers, parsed_resp)
                          for headers, parsed_resp in data_group
                          if cls._get_content_disposition(headers).category != Category.CONTENT]
        if len(metadata_parts) == 0:
            metadata_parts = None
        return content_part, metadata_parts

    @classmethod
    def _parse_metadata(
            cls,
            metadata_parts: list[tuple] | None
    ) -> Metadata | None:
        if not metadata_parts:
            return None
        if len(metadata_parts) == 1:
            headers, parsed_response = metadata_parts[0]
            content_disp = cls._get_content_disposition(headers)
            if content_disp.category == Category.METADATA:
                parsed_response["metadata_values"] = parsed_response["metadataValues"]
                del parsed_response["metadataValues"]
                return Metadata(**parsed_response)
