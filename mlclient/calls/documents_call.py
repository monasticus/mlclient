"""The ML Documents Resource Calls module.

It exports 1 class:
    * DocumentsGetCall
        A GET request to retrieve documents' content or metadata.
    * DocumentsPostCall
        A POST request to insert or update documents' content or metadata.
    * DocumentsDeleteCall
        A DELETE request to remove documents, or reset document metadata.
"""

from __future__ import annotations

import json
from typing import ClassVar

import urllib3
from urllib3.fields import RequestField

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall
from mlclient.constants import HEADER_JSON
from mlclient.structures.calls import (
    Category,
    ContentDispositionSerializer,
    DocumentsBodyPart,
)


class DocumentsGetCall(ResourceCall):
    """A GET request to retrieve documents' content or metadata.

    A ResourceCall implementation representing a single GET request
    to the /v1/documents REST Resource.

    Retrieve document content and/or metadata from the database.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/v1/documents
    """

    _ENDPOINT: str = "/v1/documents"

    _URI_PARAM: str = "uri"
    _DATABASE_PARAM: str = "database"
    _CATEGORY_PARAM: str = "category"
    _FORMAT_PARAM: str = "format"
    _TIMESTAMP_PARAM: str = "timestamp"
    _TRANSFORM_PARAM: str = "transform"
    _TXID_PARAM: str = "txid"
    _TRANS_PARAM_PREFIX: str = "trans:"

    _SUPPORTED_FORMATS: ClassVar[list] = ["binary", "json", "text", "xml"]
    _SUPPORTED_METADATA_FORMATS: ClassVar[list] = ["json", "xml"]
    _SUPPORTED_CATEGORIES: ClassVar[list] = [category.value for category in Category]

    def __init__(
        self,
        uri: str | list,
        database: str | None = None,
        category: str | list | None = None,
        data_format: str | None = None,
        timestamp: str | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        txid: str | None = None,
    ):
        """Initialize DocumentsGetCall instance.

        Parameters
        ----------
        uri : str | list
            One or more URIs for documents in the database.
            If you specify multiple URIs, the Accept header must be multipart/mixed.
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        category : str | list
            The category of data to fetch about the requested document.
            Category can be specified multiple times to retrieve any combination
            of content and metadata. Valid categories: content (default), metadata,
            metadata-values, collections, permissions, properties, and quality.
            Use metadata to request all categories except content.
        data_format : str
            The expected format of metadata returned in the response.
            Accepted values: xml or json.
            This parameter does not affect document content.
            For metadata, this parameter overrides the MIME type in the Accept header,
            except when the Accept header is multipart/mixed.
        timestamp : str
            A timestamp returned in the ML-Effective-Timestamp header of a previous
            request. Use this parameter to fetch documents based on the contents
            of the database at a fixed point-in-time.
        transform : str
            Names a content transformation previously installed via
            the /config/transforms service. The service applies the transformation
            to all documents prior to constructing the response.
        transform_params : str
            A transform parameter names and values. For example, { "myparam": 1 }.
            Transform parameters are passed to the transform named in the transform
            parameter.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request. Use the /transactions service to create and manage
            multi-statement transactions.
        """
        self._validate_params(category, data_format)

        super().__init__(method="GET")
        accept_header = self._get_accept_header(uri, category, data_format)
        self.add_header(constants.HEADER_NAME_ACCEPT, accept_header)
        self.add_param(self._URI_PARAM, uri)
        self.add_param(self._DATABASE_PARAM, database)
        self.add_param(self._CATEGORY_PARAM, category)
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._TIMESTAMP_PARAM, timestamp)
        self.add_param(self._TRANSFORM_PARAM, transform)
        self.add_param(self._TXID_PARAM, txid)
        if transform_params:
            for trans_param_name, value in transform_params.items():
                param = self._TRANS_PARAM_PREFIX + trans_param_name
                self.add_param(param, value)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Documents call.

        Returns
        -------
        str
            A Documents call endpoint
        """
        return self._ENDPOINT

    @classmethod
    def _validate_params(
        cls,
        category: str | list | None,
        data_format: str,
    ):
        categories = [category] if not isinstance(category, list) else category
        if any(cat and cat not in cls._SUPPORTED_CATEGORIES for cat in categories):
            joined_supported_categories = ", ".join(cls._SUPPORTED_CATEGORIES)
            msg = f"The supported categories are: {joined_supported_categories}"
            raise exceptions.WrongParametersError(msg)
        if data_format and data_format not in cls._SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(cls._SUPPORTED_FORMATS)
            msg = f"The supported formats are: {joined_supported_formats}"
            raise exceptions.WrongParametersError(msg)
        if (
            category
            and category != "content"
            and data_format
            and data_format not in cls._SUPPORTED_METADATA_FORMATS
        ):
            joined_supported_formats = ", ".join(cls._SUPPORTED_METADATA_FORMATS)
            msg = f"The supported metadata formats are: {joined_supported_formats}"
            raise exceptions.WrongParametersError(msg)

    @staticmethod
    def _get_accept_header(
        uri: str | list,
        category: str | list,
        data_format: str,
    ):
        if (
            not isinstance(uri, str)
            and len(uri) > 1
            or isinstance(category, list)
            and len(category) > 1
        ):
            return constants.HEADER_MULTIPART_MIXED
        if data_format and category and category != "content":
            return utils.get_accept_header_for_format(data_format)
        return None


class DocumentsPostCall(ResourceCall):
    """A POST request to insert or update documents' content or metadata.

    A ResourceCall implementation representing a single POST request
    to the /v1/documents REST Resource.

    Insert or update content and/or metadata for multiple documents in a single request.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/v1/documents
    """

    _ENDPOINT: str = "/v1/documents"

    _DATABASE_PARAM: str = "database"
    _TRANSFORM_PARAM: str = "transform"
    _TXID_PARAM: str = "txid"
    _TEMPORAL_COLLECTION_PARAM: str = "temporal-collection"
    _SYSTEM_TIME_PARAM: str = "system-time"
    _TRANS_PARAM_PREFIX: str = "trans:"

    def __init__(
        self,
        body_parts: list[DocumentsBodyPart],
        database: str | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        txid: str | None = None,
        temporal_collection: str | None = None,
        system_time: str | None = None,
    ):
        """Initialize DocumentsPostCall instance.

        Parameters
        ----------
        body_parts : list[DocumentsBodyPart]
            A list of multipart request body parts
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        transform : str
            Names a content transformation previously installed via
            the /config/transforms service. The service applies the transformation
            to all documents prior to constructing the response.
        transform_params : str
            A transform parameter names and values. For example, { "myparam": 1 }.
            Transform parameters are passed to the transform named in the transform
            parameter.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request. Use the /transactions service to create and manage
            multi-statement transactions.
        temporal_collection : str
            Specify the name of a temporal collection into which the documents are
            to be inserted.
        system_time : str
            Set the system start time for the insertion or update.
            This time will override the system time set by MarkLogic.
            Ignored if temporal-collection is not included in the request.
        """
        self._validate_params(body_parts)

        super().__init__(method="POST")
        self.add_header(constants.HEADER_NAME_ACCEPT, HEADER_JSON)
        self.add_param(self._DATABASE_PARAM, database)
        self.add_param(self._TRANSFORM_PARAM, transform)
        self.add_param(self._TXID_PARAM, txid)
        self.add_param(self._TEMPORAL_COLLECTION_PARAM, temporal_collection)
        self.add_param(self._SYSTEM_TIME_PARAM, system_time)
        if transform_params:
            for trans_param_name, value in transform_params.items():
                param = self._TRANS_PARAM_PREFIX + trans_param_name
                self.add_param(param, value)
        body, content_type = self._build_body(body_parts)
        self.add_header(constants.HEADER_NAME_CONTENT_TYPE, content_type)
        self.body = body

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Documents call.

        Returns
        -------
        str
            A Documents call endpoint
        """
        return self._ENDPOINT

    @classmethod
    def _validate_params(
        cls,
        body: list[DocumentsBodyPart] | None,
    ):
        if body is None or len(body) == 0:
            msg = "No request body provided for POST /v1/documents!"
            raise exceptions.WrongParametersError(msg)

    @classmethod
    def _build_body(
        cls,
        body_parts: list[DocumentsBodyPart],
    ) -> tuple[bytes, str]:
        fields = [cls._get_request_field(body_part) for body_part in body_parts]
        body, content_type = urllib3.encode_multipart_formdata(fields)
        return body, content_type.replace("multipart/form-data", "multipart/mixed")

    @staticmethod
    def _get_request_field(
        body_part: DocumentsBodyPart,
    ) -> RequestField:
        data = body_part.content
        if isinstance(data, dict):
            data = json.dumps(data)
        content_disp = ContentDispositionSerializer.deserialize(
            body_part.content_disposition,
        )
        return RequestField(
            name="--ignore--",
            data=data,
            headers={
                "Content-Disposition": content_disp,
                "Content-Type": body_part.content_type,
            },
        )


class DocumentsDeleteCall(ResourceCall):
    """A DELETE request to remove documents, or reset document metadata.

    A ResourceCall implementation representing a single DELETE request
    to the /v1/documents REST Resource.

    Retrieve document content and/or metadata from the database.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/DELETE/v1/documents
    """

    _ENDPOINT: str = "/v1/documents"

    _URI_PARAM: str = "uri"
    _DATABASE_PARAM: str = "database"
    _CATEGORY_PARAM: str = "category"
    _TXID_PARAM: str = "txid"
    _TEMPORAL_COLLECTION_PARAM: str = "temporal-collection"
    _SYSTEM_TIME_PARAM: str = "system-time"
    _RESULT_PARAM: str = "result"

    _SUPPORTED_CATEGORIES: ClassVar[list] = [category.value for category in Category]

    def __init__(
        self,
        uri: str | list,
        database: str | None = None,
        category: str | list | None = None,
        txid: str | None = None,
        temporal_collection: str | None = None,
        system_time: str | None = None,
        wipe_temporal: bool | None = None,
    ):
        """Initialize DocumentsDeleteCall instance.

        Parameters
        ----------
        uri : str | list
            The URI of a document to delete or for which to remove metadata.
            You can specify multiple documents.
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        category : str | list
            The category of data to remove/reset.
            Category may be specified multiple times to remove or reset
            any combination of content and metadata.
            Valid categories: content (default), metadata, metadata-values,
            collections, permissions, properties, and quality.
            Use metadata to reset all metadata.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request. Use the /transactions service to create and manage
            multi-statement transactions.
        temporal_collection : str
            Specify the name of a temporal collection that contains the document(s)
            to be deleted. Applies to all documents when deleting more than one.
        system_time : str
            Set the system start time for the insertion or update.
            This time will override the system time set by MarkLogic.
            Ignored if temporal-collection is not included in the request.
            Applies to all documents when deleting more than one.
        wipe_temporal : bool
            Remove all versions of a temporal document rather than performing
            a temporal delete. You can only use this parameter when you also specify
            a temporal-collection parameter.
        """
        self._validate_params(category)

        super().__init__(method="DELETE")
        self.add_param(self._URI_PARAM, uri)
        self.add_param(self._DATABASE_PARAM, database)
        self.add_param(self._CATEGORY_PARAM, category)
        self.add_param(self._TXID_PARAM, txid)
        self.add_param(self._TEMPORAL_COLLECTION_PARAM, temporal_collection)
        self.add_param(self._SYSTEM_TIME_PARAM, system_time)
        if wipe_temporal is True:
            self.add_param(self._RESULT_PARAM, "wiped")

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Documents call.

        Returns
        -------
        str
            A Documents call endpoint
        """
        return self._ENDPOINT

    @classmethod
    def _validate_params(
        cls,
        category: str,
    ):
        categories = [category] if not isinstance(category, list) else category
        if any(cat and cat not in cls._SUPPORTED_CATEGORIES for cat in categories):
            joined_supported_categories = ", ".join(cls._SUPPORTED_CATEGORIES)
            msg = f"The supported categories are: {joined_supported_categories}"
            raise exceptions.WrongParametersError(msg)
