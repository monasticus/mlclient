from __future__ import annotations

from typing import Any, Iterator

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
            uris: str | list[str] | tuple[str] | set[str],
            category: str | list | None = None,
    ) -> Document | list[Document]:
        call = self._get_call(uris=uris, category=category)
        resp = self.call(call)
        return self._parse(resp, uris, category)

    @classmethod
    def _get_call(
            cls,
            uris: str | list[str] | tuple[str] | set[str],
            category: str | list | None,
    ) -> DocumentsGetCall:
        params = {
            "uri": uris,
            "category": category,
        }
        if (category and category != "content" or
                isinstance(category, list) and category != ["content"]):
            params["data_format"] = "json"

        return DocumentsGetCall(**params)

    @classmethod
    def _parse(
            cls,
            resp: Response,
            uris: str | list[str] | tuple[str] | set[str],
            category: str | list | None,
    ) -> Document | list[Document]:
        parsed_resp = cls._parse_response(resp)
        content_type = cls._get_response_content_type(resp)
        is_multipart = content_type.startswith(constants.HEADER_MULTIPART_MIXED)
        documents_data = cls._pre_format_data(parsed_resp, is_multipart, uris, category)
        docs = cls._parse_to_documents(documents_data)
        if isinstance(uris, str):
            return docs[0]
        return docs

    @classmethod
    def _get_response_content_type(
            cls,
            resp: Response,
    ) -> str | None:
        return next((value
                     for name, value in resp.headers.items()
                     if name.lower() == "content-type"), None)

    @classmethod
    def _parse_response(
            cls,
            resp: Response,
    ) -> list[tuple]:
        if not resp.ok:
            resp_body = resp.json()
            raise MarkLogicError(resp_body["errorResponse"])
        parsed_resp = MLResponseParser.parse_with_headers(resp)
        if isinstance(parsed_resp, tuple):
            return [parsed_resp]
        return parsed_resp

    @classmethod
    def _pre_format_data(
            cls,
            parsed_resp: list[tuple],
            is_multipart: bool,
            origin_uris: str | list[str] | tuple[str] | set[str],
            origin_category: str | list | None,
    ) -> Iterator[dict]:
        if is_multipart:
            return cls._pre_format_documents(parsed_resp, origin_category)
        return cls._pre_format_document(
            parsed_resp,
            origin_uris,
            origin_category)

    @classmethod
    def _pre_format_documents(
            cls,
            parsed_resp: list[tuple],
            origin_category: str | list | None,
    ) -> Iterator[dict]:
        expect_content, expect_metadata = cls._expect_categories(origin_category)
        pre_formatted_data = {}
        for headers, parse_resp_body in parsed_resp:
            content_disp = cls._get_content_disposition(headers)
            partial_data = cls._get_partial_data(content_disp, parse_resp_body)

            if not (expect_content and expect_metadata):
                yield partial_data
            elif content_disp.filename not in pre_formatted_data:
                pre_formatted_data[content_disp.filename] = partial_data
            else:
                data = pre_formatted_data[content_disp.filename]
                if content_disp.category == Category.CONTENT:
                    data.update(partial_data)
                    yield data
                else:
                    partial_data.update(data)
                    yield partial_data

    @classmethod
    def _pre_format_document(
            cls,
            parsed_resp: list[tuple],
            origin_uris: str | list[str] | tuple[str] | set[str],
            origin_category: str | list | None,
    ) -> Iterator[dict]:
        headers, parsed_resp_body = parsed_resp[0]
        uri = origin_uris[0] if isinstance(origin_uris, list) else origin_uris
        expect_content, _ = cls._expect_categories(origin_category)
        if expect_content:
            yield {
                "uri": uri,
                "format": headers.get(constants.HEADER_NAME_ML_DOCUMENT_FORMAT),
                "content": parsed_resp_body,
            }
        else:
            yield {
                "uri": uri,
                "metadata": cls._parse_metadata(parsed_resp_body),
            }

    @classmethod
    def _expect_categories(
            cls,
            origin_category: str | list | None,
    ) -> tuple[bool, bool]:
        expect_content = (not origin_category or
                          Category.CONTENT.value in origin_category)
        expect_metadata = origin_category and any(cat.value in origin_category
                                                  for cat in Category
                                                  if cat != cat.CONTENT)
        return expect_content, expect_metadata

    @classmethod
    def _get_partial_data(
            cls,
            content_disp: DocumentsContentDisposition,
            parsed_resp_body: Any,
    ) -> dict:
        if content_disp.category == Category.CONTENT:
            return {
                "uri": content_disp.filename,
                "format": content_disp.format_,
                "content": parsed_resp_body,
            }
        return {
            "uri": content_disp.filename,
            "metadata": cls._parse_metadata(parsed_resp_body),
        }

    @classmethod
    def _parse_metadata(
            cls,
            raw_metadata: dict,
    ) -> Metadata:
        if "metadataValues" in raw_metadata:
            raw_metadata["metadata_values"] = raw_metadata["metadataValues"]
            del raw_metadata["metadataValues"]

        return Metadata(**raw_metadata)

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
        content = document_data.get("content")
        metadata = document_data.get("metadata")
        if content:
            return DocumentFactory.build_document(content=content,
                                                  doc_type=doc_format,
                                                  uri=uri,
                                                  metadata=metadata)
        return MetadataDocument(uri=uri,
                                metadata=metadata)
