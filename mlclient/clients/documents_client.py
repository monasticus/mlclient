from __future__ import annotations

import xml.etree.ElementTree as ElemTree

from mlclient import constants
from mlclient.calls import DocumentsGetCall
from mlclient.clients import MLResourceClient, MLResponseParser
from mlclient.model import (BytesDocument, Document, DocumentType,
                            JSONDocument, StringDocument, XMLDocument)


class DocumentsClient(MLResourceClient):

    def read(
            self,
            uri: str | list[str] | tuple[str] | set[str],
    ) -> Document | list[Document]:
        call = self._get_call(uri=uri)
        resp = self.call(call)
        if isinstance(uri, (list, tuple, set)) and len(uri) == 1:
            uri = uri[0]

        if isinstance(uri, str):
            headers, parsed_resp = MLResponseParser.parse_with_headers(resp)
            return self._parse_to_document(uri, headers, parsed_resp)
        return []

    @classmethod
    def _get_call(
            cls,
            uri: str,
    ):
        params = {
            "uri": uri,
        }

        return DocumentsGetCall(**params)

    @classmethod
    def _parse_to_document(
            cls,
            uri: str,
            headers: dict,
            parsed_resp: ElemTree.ElementTree | dict | str | bytes,
    ):
        doc_format = headers.get(constants.HEADER_NAME_ML_DOCUMENT_FORMAT)
        doc_type = DocumentType(doc_format)
        if doc_type == DocumentType.XML:
            impl = XMLDocument
        elif doc_type == DocumentType.JSON:
            impl = JSONDocument
        elif doc_type == DocumentType.TEXT:
            impl = StringDocument
        else:
            impl = BytesDocument

        return impl(parsed_resp, uri=uri, doc_type=doc_type)
