from __future__ import annotations

import xml.etree.ElementTree as ElemTree

from requests import Response

from mlclient import constants
from mlclient.calls import DocumentsGetCall
from mlclient.clients import MLResourceClient, MLResponseParser
from mlclient.exceptions import MarkLogicError
from mlclient.model import (BinaryDocument, Document, DocumentType,
                            JSONDocument, TextDocument, XMLDocument)


class DocumentsClient(MLResourceClient):

    def read(
            self,
            uri: str | list[str] | tuple[str] | set[str],
    ) -> Document | list[Document]:
        call = self._get_call(uri=uri)
        resp = self.call(call)
        parsed_resp_with_headers = self._parse_response(resp)
        docs = self._parse_to_documents(uri, parsed_resp_with_headers)
        if len(docs) == 1:
            docs = docs[0]
        return docs

    @classmethod
    def _get_call(
            cls,
            uri: str | list[str] | tuple[str] | set[str],
    ):
        params = {
            "uri": uri,
        }

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
            parsed_resp_with_headers: list[tuple],
    ) -> list[Document]:
        return [cls._parse_to_document(uri, headers, parsed_resp)
                for headers, parsed_resp in parsed_resp_with_headers
                if parsed_resp != []]

    @classmethod
    def _parse_to_document(
            cls,
            uri: str | list[str] | tuple[str] | set[str],
            headers: dict,
            parsed_resp: ElemTree.ElementTree | dict | str | bytes,
    ) -> Document:
        single_doc = isinstance(uri, str) or len(uri) == 1
        if single_doc:
            uri = uri if isinstance(uri, str) else uri[0]
            doc_format = headers.get(constants.HEADER_NAME_ML_DOCUMENT_FORMAT)
        else:
            content_disp = headers.get(constants.HEADER_NAME_CONTENT_DISP).split("; ")
            disp_dict = {disp.split("=")[0]: disp.split("=")[1]
                         for disp in content_disp
                         if len(disp.split("=")) > 1}
            uri = disp_dict.get("filename")[1:-1]
            doc_format = disp_dict.get("format")

        doc_type = DocumentType(doc_format)
        if doc_type == DocumentType.XML:
            impl = XMLDocument
        elif doc_type == DocumentType.JSON:
            impl = JSONDocument
        elif doc_type == DocumentType.TEXT:
            impl = TextDocument
        else:
            impl = BinaryDocument

        return impl(parsed_resp, uri=uri)
