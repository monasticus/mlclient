from abc import ABCMeta, abstractmethod


class ResourceCall(metaclass=ABCMeta):

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'ENDPOINT') and
                hasattr(subclass, 'endpoint') and
                callable(subclass.endpoint) or
                NotImplemented)

    def __init__(self, params: dict = None, headers: dict = None, body=None,
                 accept: str = None, content_type: str = None):
        self.__params = params or {}
        self.__headers = headers or {}
        self.__body = body
        if accept:
            self.__headers["accept"] = accept
        if content_type:
            self.__headers["content-type"] = content_type

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

    def params(self):
        return self.__params.copy()

    def headers(self):
        return self.__headers.copy()

    def body(self):
        return self.__body
