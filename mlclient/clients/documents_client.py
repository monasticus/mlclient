from __future__ import annotations

from mlclient.calls import DocumentsGetCall
from mlclient.clients import MLResourceClient, MLResponseParser
from mlclient.exceptions import MarkLogicError
from mlclient.mimetypes import Mimetypes
from mlclient.model import (BytesDocument, Document, DocumentType,
                            JSONDocument, StringDocument, XMLDocument)


class DocumentsClient(MLResourceClient):

    def read(
            self,
            uri: str,
    ) -> Document:
        call = self._get_call(uri=uri)
        resp = self.call(call)
        parsed_resp = MLResponseParser.parse(resp)
        if not resp.ok:
            raise MarkLogicError(parsed_resp["errorResponse"])
        content_type = resp.headers.get("Content-Type")
        doc_type = Mimetypes.get_doc_type(content_type)
        if doc_type == DocumentType.XML:
            impl = XMLDocument
        elif doc_type == DocumentType.JSON:
            impl = JSONDocument
        elif doc_type == DocumentType.TEXT:
            impl = StringDocument
        elif doc_type == DocumentType.BINARY:
            impl = BytesDocument

        return impl(parsed_resp, uri=uri, doc_type=doc_type)

    @classmethod
    def _get_call(
            cls,
            uri: str,
    ):
        params = {
            "uri": uri,
        }

        return DocumentsGetCall(**params)
