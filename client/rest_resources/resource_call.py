from abc import ABCMeta, abstractmethod
from client import constants


class ResourceCall(metaclass=ABCMeta):

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'ENDPOINT') and
                hasattr(subclass, 'endpoint') and
                callable(subclass.endpoint) or
                NotImplemented)

    def __init__(self, method: str = constants.METHOD_GET, params: dict = None, headers: dict = None,
                 body=None, accept: str = None, content_type: str = None):
        self.__method = method
        self.__params = params or {}
        self.__headers = headers or {}
        self.__body = body
        if accept:
            self.__headers[constants.HEADER_ACCEPT] = accept
        if content_type:
            self.__headers[constants.HEADER_CONTENT_TYPE] = content_type

    @abstractmethod
    def endpoint(self):
        raise NotImplementedError

    def add_param(self, param_name: str, param_value):
        if param_name and param_value:
            self.__params[param_name] = param_value
        return self

    def add_header(self, header_name: str, header_value):
        if header_name and header_value:
            self.__headers[header_name] = header_value
        return self

    def set_body(self, body):
        self.__body = body

    def method(self):
        return self.__method

    def params(self):
        return self.__params.copy()

    def headers(self):
        return self.__headers.copy()

    def body(self):
        if isinstance(self.__body, str):
            return self.__body
        elif isinstance(self.__body, dict):
            return self.__body.copy()
