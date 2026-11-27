"""The ML Documents Api Calls module.

It exports 4 classes:
    * DocumentsGetCall
        A GET request to retrieve documents' content or metadata.
    * DocumentsHeadCall
        A HEAD request to get the headers a GET of one document would return.
    * DocumentsPostCall
        A POST request to insert or update documents' content or metadata.
    * DocumentsDeleteCall
        A DELETE request to remove documents, or reset document metadata.
"""

from __future__ import annotations

import json
from typing import ClassVar

from mlclient import _constants as constants
from mlclient import _utils as utils
from mlclient import exceptions
from mlclient.calls import _utils as call_utils
from mlclient.calls.base import ApiCall
from mlclient.models.document_parts import Category, DocumentsBodyPart
from mlclient.multipart import MultipartPart, encode_multipart_mixed


class DocumentsGetCall(ApiCall):
    """A GET request to retrieve documents' content or metadata.

    An ApiCall implementation representing a single GET request
    to the /v1/documents endpoint.

    Retrieve document content and/or metadata from the database.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/v1/documents
    """

    _API_VERSION: int = 1

    _ENDPOINT: str = "/v{}/documents"

    _URI_PARAM: str = "uri"
    _DATABASE_PARAM: str = "database"
    _CATEGORY_PARAM: str = "category"
    _FORMAT_PARAM: str = "format"
    _TIMESTAMP_PARAM: str = "timestamp"
    _TRANSFORM_PARAM: str = "transform"
    _TXID_PARAM: str = "txid"

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
    ) -> None:
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
            Metadata accepts xml or json. Content-only reads also accept text
            and binary; these values do not convert the stored content.
            This parameter does not affect document content.
            For metadata, this parameter overrides the MIME type in the Accept header,
            except when the Accept header is multipart/mixed.
        timestamp : str
            A timestamp returned in the ML-Effective-Timestamp header of a previous
            request. Use this parameter to fetch documents based on the contents
            of the database at a fixed point-in-time. Cannot be combined with txid.
        transform : str
            Names a content transformation previously installed via
            the /config/transforms service. The service applies the transformation
            to all documents prior to constructing the response.
        transform_params : dict
            A transform parameter names and values. For example, { "myparam": 1 }.
            Transform parameters are passed to the transform named in the transform
            parameter.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request. Use the /transactions service to create and manage
            multi-statement transactions.
        """
        categories = self._categories_list(category)
        self._validate_params(
            categories,
            data_format,
            timestamp,
            txid,
            transform,
            transform_params,
        )

        super().__init__(method="GET")
        accept_header = self._get_accept_header(uri, categories, data_format)
        self.add_header(constants.HEADER_NAME_ACCEPT, accept_header)
        self.add_param(self._URI_PARAM, uri)
        self.add_param(self._DATABASE_PARAM, database)
        self.add_param(self._CATEGORY_PARAM, category)
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._TIMESTAMP_PARAM, timestamp)
        self.add_param(self._TRANSFORM_PARAM, transform)
        self.add_param(self._TXID_PARAM, txid)
        self._params.update(call_utils.query_params({}, transform_params))

    @property
    def endpoint(
        self,
    ) -> str:
        """An endpoint for the Documents call.

        Returns
        -------
        str
            A Documents call endpoint
        """
        return self._ENDPOINT.format(self._API_VERSION)

    @staticmethod
    def _categories_list(category: str | list | None) -> list:
        """Return the requested categories as a list.

        Parameters
        ----------
        category : str | list | None
            One category or several, as passed to the constructor.

        Returns
        -------
        list
            The categories; None, an empty string and an empty list mean content,
            the server default.
        """
        if not category:
            return [Category.CONTENT.value]
        if isinstance(category, list):
            return category
        return [category]

    @classmethod
    def _validate_params(
        cls,
        categories: list[str],
        data_format: str | None,
        timestamp: str | None,
        txid: str | None,
        transform: str | None,
        transform_params: dict | None,
    ) -> None:
        """Reject parameters and combinations MarkLogic does not accept.

        A point-in-time read inside a transaction fails on the server with a 500
        ``XDMP-UPDATETIMESTAMP`` error, so it is rejected before any request.

        Parameters
        ----------
        categories : list
            The requested categories.
        data_format : str | None
            The metadata format; None leaves it to the server.
        timestamp : str | None
            The point in time to read at.
        txid : str | None
            The multi-statement transaction identifier.
        transform : str | None
            Installed transform name.
        transform_params : dict | None
            Parameters requiring a transform.

        Raises
        ------
        WrongParametersError
            If a category or format is unsupported, metadata requests use a format
            other than json or xml, or timestamp is combined with txid.
        """
        call_utils.validate_supported(
            categories,
            cls._SUPPORTED_CATEGORIES,
            "categories",
        )
        if data_format:
            call_utils.validate_supported(
                [data_format],
                cls._SUPPORTED_FORMATS,
                "formats",
            )
            if any(category != Category.CONTENT.value for category in categories):
                call_utils.validate_supported(
                    [data_format],
                    cls._SUPPORTED_METADATA_FORMATS,
                    "metadata formats",
                )
        if timestamp is not None and txid is not None:
            msg = "timestamp cannot be combined with txid"
            raise exceptions.WrongParametersError(msg)
        _validate_transform_params(transform, transform_params)

    @staticmethod
    def _get_accept_header(
        uri: str | list,
        categories: list[str],
        data_format: str | None,
    ) -> str | None:
        """Return the Accept header for the requested documents and categories.

        Parameters
        ----------
        uri : str | list
            One or more document URIs.
        categories : list
            The requested categories.
        data_format : str | None
            The metadata format.

        Returns
        -------
        str | None
            multipart/mixed for several documents or categories, the format's
            MIME type for metadata of a single document, otherwise None.
        """
        if (not isinstance(uri, str) and len(uri) > 1) or len(categories) > 1:
            return constants.HEADER_MULTIPART_MIXED
        if data_format and categories != [Category.CONTENT.value]:
            return utils.get_accept_header_for_format(data_format)
        return None


class DocumentsHeadCall(ApiCall):
    """A HEAD request to get the headers a GET of one document would return.

    An ApiCall implementation representing a single HEAD request
    to the /v1/documents endpoint.

    Returns the same headers as an equivalent GET (content/metadata fetch)
    on the /documents service, without a body: status 200 (OK) when the document
    exists, 404 (Not Found) when it does not.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/HEAD/v1/documents
    """

    _API_VERSION: int = 1

    _ENDPOINT: str = "/v{}/documents"

    def __init__(
        self,
        uri: str,
        database: str | None = None,
        category: str | list | None = None,
        data_format: str | None = None,
        txid: str | None = None,
    ) -> None:
        """Initialize DocumentsHeadCall instance.

        The request carries the parameters and the Accept header of the
        equivalent DocumentsGetCall, so MarkLogic answers with that GET's headers.

        Parameters
        ----------
        uri : str
            The URI of a document in the database. MarkLogic accepts a single URI
            per request.
        database : str
            Perform this operation on the named content database instead
            of the default content database associated with the REST API instance.
            Using an alternative database requires the "eval-in" privilege.
        category : str | list
            The category of data for which to generate headers. Category can be
            specified multiple times to request any combination of content
            and metadata. Valid categories: content (default), metadata,
            metadata-values, collections, permissions, properties, and quality.
            Use metadata to request all categories except content.
        data_format : str
            The format of metadata whose headers are generated: xml or json.
            Content-only requests also accept text and binary without converting
            the stored content or changing its Content-Type.
        txid : str
            The transaction identifier of the multi-statement transaction in which
            to service this request. Use the /transactions service to create and manage
            multi-statement transactions.

        Raises
        ------
        WrongParametersError
            If a category or format is unsupported, or a metadata request
            uses a format other than json or xml.
        """
        equivalent_get = DocumentsGetCall(
            uri=uri,
            database=database,
            category=category,
            data_format=data_format,
            txid=txid,
        )
        super().__init__(
            method=constants.METHOD_HEAD,
            params=equivalent_get.params,
            headers=equivalent_get.headers,
        )

    @property
    def endpoint(
        self,
    ) -> str:
        """An endpoint for the Documents call.

        Returns
        -------
        str
            A Documents call endpoint
        """
        return self._ENDPOINT.format(self._API_VERSION)


class DocumentsPostCall(ApiCall):
    """A POST request to insert or update documents' content or metadata.

    An ApiCall implementation representing a single POST request
    to the /v1/documents endpoint.

    Insert or update content and/or metadata for multiple documents in a single request.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/v1/documents
    """

    _API_VERSION: int = 1

    _ENDPOINT: str = "/v{}/documents"

    _DATABASE_PARAM: str = "database"
    _TRANSFORM_PARAM: str = "transform"
    _TXID_PARAM: str = "txid"
    _TEMPORAL_COLLECTION_PARAM: str = "temporal-collection"
    _SYSTEM_TIME_PARAM: str = "system-time"

    def __init__(
        self,
        body_parts: list[DocumentsBodyPart],
        database: str | None = None,
        transform: str | None = None,
        transform_params: dict | None = None,
        txid: str | None = None,
        temporal_collection: str | None = None,
        system_time: str | None = None,
    ) -> None:
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
            the /config/transforms service. Transforms are applied only to content
            parts: the transform is applied to the content of a part prior to
            updating or inserting the document.
        transform_params : dict
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
        self._validate_params(
            body_parts,
            transform,
            transform_params,
            temporal_collection,
            system_time,
        )

        super().__init__(method="POST")
        self.add_header(constants.HEADER_NAME_ACCEPT, constants.HEADER_JSON)
        self.add_param(self._DATABASE_PARAM, database)
        self.add_param(self._TRANSFORM_PARAM, transform)
        self.add_param(self._TXID_PARAM, txid)
        self.add_param(self._TEMPORAL_COLLECTION_PARAM, temporal_collection)
        self.add_param(self._SYSTEM_TIME_PARAM, system_time)
        self._params.update(call_utils.query_params({}, transform_params))
        body, content_type = self._build_body(body_parts)
        self.add_header(constants.HEADER_NAME_CONTENT_TYPE, content_type)
        self.body = body

    @property
    def endpoint(
        self,
    ) -> str:
        """An endpoint for the Documents call.

        Returns
        -------
        str
            A Documents call endpoint
        """
        return self._ENDPOINT.format(self._API_VERSION)

    @classmethod
    def _validate_params(
        cls,
        body: list[DocumentsBodyPart] | None,
        transform: str | None,
        transform_params: dict | None,
        temporal_collection: str | None,
        system_time: str | None,
    ) -> None:
        """Validate the request body, transform parameters and temporal options.

        Parameters
        ----------
        body : list[DocumentsBodyPart] | None
            Content and metadata parts to write.
        transform : str | None
            Installed transform name.
        transform_params : dict | None
            Parameters requiring a transform.
        temporal_collection : str | None
            Temporal collection receiving the write.
        system_time : str | None
            Explicit system time requiring a temporal collection.

        Raises
        ------
        WrongParametersError
            If the body is empty or the transform/temporal options conflict.
        """
        if body is None or len(body) == 0:
            msg = "No request body provided for POST /v1/documents!"
            raise exceptions.WrongParametersError(msg)
        if system_time is not None and not temporal_collection:
            msg = "system_time requires temporal_collection"
            raise exceptions.WrongParametersError(msg)
        _validate_transform_params(transform, transform_params)

    @classmethod
    def _build_body(
        cls,
        body_parts: list[DocumentsBodyPart],
    ) -> tuple[bytes, str]:
        parts = [cls._build_multipart_part(body_part) for body_part in body_parts]
        return encode_multipart_mixed(parts)

    @staticmethod
    def _build_multipart_part(
        body_part: DocumentsBodyPart,
    ) -> MultipartPart:
        data = body_part.content
        if isinstance(data, dict):
            data = json.dumps(data)
        if isinstance(data, str):
            data = data.encode("utf-8")
        content_disp = body_part.disposition.to_header()
        return MultipartPart(
            headers={
                "Content-Disposition": content_disp,
                "Content-Type": body_part.content_type,
            },
            content=data,
        )


class DocumentsDeleteCall(ApiCall):
    """A DELETE request to remove documents, or reset document metadata.

    An ApiCall implementation representing a single DELETE request
    to the /v1/documents endpoint.

    Remove documents, or reset document metadata.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/DELETE/v1/documents
    """

    _API_VERSION: int = 1

    _ENDPOINT: str = "/v{}/documents"

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
    ) -> None:
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

        Raises
        ------
        WrongParametersError
            If a category, including an empty string, is not supported.
        """
        call_utils.validate_supported(
            category,
            self._SUPPORTED_CATEGORIES,
            "categories",
        )

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
    ) -> str:
        """An endpoint for the Documents call.

        Returns
        -------
        str
            A Documents call endpoint
        """
        return self._ENDPOINT.format(self._API_VERSION)


def _validate_transform_params(
    transform: str | None,
    transform_params: dict | None,
) -> None:
    """Reject transform parameters sent without a transform to receive them.

    Parameters
    ----------
    transform : str | None
        Name of an installed transform.
    transform_params : dict | None
        Parameters for the transform.

    Raises
    ------
    WrongParametersError
        If transform_params are given without transform.
    """
    if transform_params and not transform:
        msg = "transform_params require transform"
        raise exceptions.WrongParametersError(msg)
