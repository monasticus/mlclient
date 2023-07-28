"""The ML Resource Call module.

It exports 1 class:
* ResourceCall
    An abstract class representing a single request to a MarkLogic REST Resource.
"""
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any, Union

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
    set_body(body: Union[str, dict])
        Set a request body
    method() -> str
        Return a request method
    params() -> dict
        Return request parameters
    headers() -> dict
        Return request headers
    body() -> Union[str, dict]
        Return a request body
    """

    def __init__(
            self,
            method: str = constants.METHOD_GET,
            params: dict = None,
            headers: dict = None,
            body: Union[str, dict] = None,
            accept: str = None,
            content_type: str = None
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
        body : Union[str, dict]
            a request body
        accept : str
            an Accept header value
        content_type : str
            a Content-Type header value
        """
        self.__method = method
        self.__params = params or {}
        self.__headers = headers or {}
        self.__body = body
        if accept:
            self.__headers[constants.HEADER_NAME_ACCEPT] = accept
        if content_type:
            self.__headers[constants.HEADER_NAME_CONTENT_TYPE] = content_type

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
            self
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
            param_value: Any
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
            self.__params[param_name] = param_value

    def add_header(
            self,
            header_name: str,
            header_value: Any
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
            self.__headers[header_name] = header_value

    def set_body(
            self,
            body: Union[str, dict]
    ):
        """Set a request body.

        Parameters
        ----------
        body : Union[str, dict]
            a request body
        """
        self.__body = body

    def method(
            self
    ) -> str:
        """Return a request method.

        Returns
        -------
        str
            a request method
        """
        return self.__method

    def params(
            self
    ) -> dict:
        """Return request parameters.

        Returns
        -------
        dict
            request parameters
        """
        return self.__params.copy()

    def headers(
            self
    ) -> dict:
        """Return request headers.

        Returns
        -------
        dict
            request headers
        """
        return self.__headers.copy()

    def body(
            self
    ) -> Union[str, dict]:
        """Return a request body.

        Returns
        -------
        Union[str, dict, None]
            a request body
        """
        if isinstance(self.__body, str):
            return self.__body
        elif isinstance(self.__body, dict):
            return self.__body.copy()
