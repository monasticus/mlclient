"""The ML Resource Call module.

It exports 1 class:
* ResourceCall
    An abstract class representing a single request to a MarkLogic REST Resource.
"""
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any

from mlclient import constants


class ResourceCall(metaclass=ABCMeta):
    """An abstract class representing a single request to a MarkLogic REST Resource.

    Methods
    -------
    endpoint() -> str
        An abstract method returning an endpoint for a specific resource call
    add_param(param_name: str, param_value: Any)
        Put a request parameter if it's name and value exist
    add_header(header_name: str, header_value: Any)
        Put a request header if it's name and value exist
    set_body(body: str | dict)
        Set a request body
    method() -> str
        Return a request method
    params() -> dict
        Return request parameters
    headers() -> dict
        Return request headers
    body() -> str | dict
        Return a request body
    """

    def __init__(
            self,
            method: str = constants.METHOD_GET,
            params: dict | None = None,
            headers: dict | None = None,
            body: str | dict | None = None,
            accept: str | None = None,
            content_type: str | None = None,
    ):
        """Initialize ResourceCall implementation instance.

        Parameters
        ----------
        method : str
            a request method
        params : dict
            request parameters
        headers : dict
            request headers
        body : str | dict
            a request body
        accept : str
            an Accept header value
        content_type : str
            a Content-Type header value
        """
        self._method = method
        self._params = params or {}
        self._headers = headers or {}
        self._body = body
        if accept:
            self._headers[constants.HEADER_NAME_ACCEPT] = accept
        if content_type:
            self._headers[constants.HEADER_NAME_CONTENT_TYPE] = content_type

    @classmethod
    def __subclasshook__(
            cls,
            subclass: ResourceCall,
    ):
        """Verify if a subclass implements all abstract methods.

        Parameters
        ----------
        subclass : ResourceCall
            A ResourceCall subclass

        Returns
        -------
        bool
            True if the subclass includes the generate and stringify
            methods
        """
        return "endpoint" in subclass.__dict__ and callable(subclass.endpoint)

    @abstractmethod
    def endpoint(
            self,
    ) -> str:
        """Return an endpoint for a specific resource call.

        Returns
        -------
        str
            An endpoint
        """
        raise NotImplementedError

    def add_param(
            self,
            param_name: str,
            param_value: Any,
    ):
        """Put a request parameter if it's name and value exist.

        Parameters
        ----------
        param_name : str
            a request parameter name
        param_value : Any
            a request parameter value
        """
        if param_name and param_value:
            self._params[param_name] = param_value

    def add_header(
            self,
            header_name: str,
            header_value: Any,
    ):
        """Put a request header if it's name and value exist.

        Parameters
        ----------
        header_name : str
            a request header name
        header_value : Any
            a request header value
        """
        if header_name and header_value:
            self._headers[header_name] = header_value

    def set_body(
            self,
            body: str | dict,
    ):
        """Set a request body.

        Parameters
        ----------
        body : str | dict
            a request body
        """
        self._body = body

    def method(
            self,
    ) -> str:
        """Return a request method.

        Returns
        -------
        str
            a request method
        """
        return self._method

    def params(
            self,
    ) -> dict:
        """Return request parameters.

        Returns
        -------
        dict
            request parameters
        """
        return self._params.copy()

    def headers(
            self,
    ) -> dict:
        """Return request headers.

        Returns
        -------
        dict
            request headers
        """
        return self._headers.copy()

    def body(
            self,
    ) -> str | dict:
        """Return a request body.

        Returns
        -------
        str | dict
            a request body
        """
        if isinstance(self._body, str):
            return self._body
        if isinstance(self._body, dict):
            return self._body.copy()
        return None
