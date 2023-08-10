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
    """An abstract class representing a single request to a MarkLogic REST Resource."""

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
        self.method = method
        self.params = params
        self.headers = headers
        self.body = body
        if accept:
            self.add_header(constants.HEADER_NAME_ACCEPT, accept)
        if content_type:
            self.add_header(constants.HEADER_NAME_CONTENT_TYPE, content_type)

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
            True if the subclass includes the endpoint property
        """
        return "endpoint" in subclass.__dict__ and not callable(subclass.endpoint)

    @property
    @abstractmethod
    def endpoint(
            self,
    ) -> str:
        """An endpoint of the ResourceCall.

        Returns
        -------
        str
            An endpoint
        """
        raise NotImplementedError

    @property
    def method(
            self,
    ) -> str:
        """A request method.

        Returns
        -------
        str
            a request method
        """
        return self._method

    @method.setter
    def method(
            self,
            method: str,
    ):
        """Set a request method.

        Parameters
        ----------
        method : str
            A request method
        """
        self._method = method

    @property
    def params(
            self,
    ) -> dict:
        """Request parameters.

        Returns
        -------
        dict
            request parameters
        """
        return self._params.copy()

    @params.setter
    def params(
            self,
            params: dict,
    ):
        """Set request parameters.

        Parameters
        ----------
        params : dict
            Request parameters
        """
        self._params = {}
        if params:
            for key, value in params.items():
                self.add_param(key, value)

    @property
    def headers(
            self,
    ) -> dict:
        """Request headers.

        Returns
        -------
        dict
            request headers
        """
        return self._headers.copy()

    @headers.setter
    def headers(
            self,
            headers: dict,
    ):
        """Set request headers.

        Parameters
        ----------
        headers : dict
            Request headers
        """
        self._headers = {}
        if headers:
            for key, value in headers.items():
                self.add_header(key, value)

    @property
    def body(
            self,
    ) -> str | dict | None:
        """A request body.

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

    @body.setter
    def body(
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
