from client.rest_resources.resource_call import ResourceCall
from client.utils import get_accept_header_for_format
import client.exceptions as exc

from dateutil import parser


class LogsCall(ResourceCall):

    ENDPOINT = "/manage/v2/logs"

    __FORMAT_PARAM = "format"
    __FILENAME_PARAM = "filename"
    __HOST_PARAM = "host"
    __START_PARAM = "start"
    __END_PARAM = "end"
    __REGEX_PARAM = "regex"

    def __init__(self, data_format: str = "html", filename: str = None, host: str = None,
                 start_time: str = None, end_time: str = None, regex: str = None):
        self.__validate_params(data_format, filename, start_time, end_time)
        super().__init__(accept=get_accept_header_for_format(data_format))

        self.add_param(LogsCall.__FORMAT_PARAM, data_format)
        self.add_param(LogsCall.__FILENAME_PARAM, filename)
        self.add_param(LogsCall.__HOST_PARAM, host)
        self.add_param(LogsCall.__START_PARAM, start_time)
        self.add_param(LogsCall.__END_PARAM, end_time)
        self.add_param(LogsCall.__REGEX_PARAM, regex)

    def endpoint(self):
        return LogsCall.ENDPOINT

    @staticmethod
    def __validate_params(data_format: str, filename: str, start_time: str, end_time: str):
        if data_format not in ["xml", "json", "html"]:
            raise exc.WrongParameters("The supported formats are xml, json or html")
        if not filename:
            raise exc.WrongParameters("The filename is a mandatory parameter!")
        try:
            if start_time:
                parser.parse(start_time)
        except ValueError:
            raise exc.WrongParameters("The start parameter is not a dateTime value!")
        try:
            if end_time:
                parser.parse(end_time)
        except ValueError:
            raise exc.WrongParameters("The end parameter is not a dateTime value!")
