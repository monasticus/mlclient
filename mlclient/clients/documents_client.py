from __future__ import annotations

import xml.etree.ElementTree as ElemTree

from mlclient.calls import DocumentsGetCall
from mlclient.clients import MLResourceClient, MLResponseParser
from mlclient.exceptions import MarkLogicError


class DocumentsClient(MLResourceClient):

    def read(
            self,
            uri: str,
    ) -> ElemTree.ElementTree:
        call = self._get_call(uri=uri)
        resp = self.call(call)
        parsed_resp = MLResponseParser.parse(resp)
        if not resp.ok:
            raise MarkLogicError(parsed_resp["errorResponse"])
        return parsed_resp

    @classmethod
    def _get_call(
            cls,
            uri: str,
    ):
        params = {
            "uri": uri,
        }

        return DocumentsGetCall(**params)
