from dateutil import parser

from mlclient import exceptions, utils
from mlclient.calls import ResourceCall


class LogsCall(ResourceCall):
    """
    A ResourceCall implementation representing a single request to the /manage/v2/logs REST Resource

    Returns the content of server log files.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/logs

    Attributes
    ----------
    ENDPOINT
        a static constant storing the Logs endpoint value

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    ENDPOINT = "/manage/v2/logs"

    __FORMAT_PARAM = "format"
    __FILENAME_PARAM = "filename"
    __HOST_PARAM = "host"
    __START_PARAM = "start"
    __END_PARAM = "end"
    __REGEX_PARAM = "regex"

    def __init__(self, filename: str, data_format: str = "html", host: str = None,
                 start_time: str = None, end_time: str = None, regex: str = None):
        """
        Parameters
        ----------
        filename : str
            The log file to be returned.
        data_format : str
            The format of the data in the log file. The supported formats are xml, json or html.
        host : str
            The host from which to return the log data.
        start_time : str
            The start time for the log data.
        end_time : str
            The end time for the log data.
        regex : str
            Filters the log data, based on a regular expression.
        """

        data_format = data_format if data_format is not None else "html"
        LogsCall.__validate_params(data_format, start_time, end_time)

        super().__init__(accept=utils.get_accept_header_for_format(data_format))
        self.add_param(LogsCall.__FORMAT_PARAM, data_format)
        self.add_param(LogsCall.__FILENAME_PARAM, filename)
        self.add_param(LogsCall.__HOST_PARAM, host)
        self.add_param(LogsCall.__START_PARAM, LogsCall.__reformat_datetime_param(start_time))
        self.add_param(LogsCall.__END_PARAM, LogsCall.__reformat_datetime_param(end_time))
        self.add_param(LogsCall.__REGEX_PARAM, regex)

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Logs call

        Returns
        -------
        str
            an Logs call endpoint
        """

        return LogsCall.ENDPOINT

    @staticmethod
    def __validate_params(data_format: str, start_time: str, end_time: str):
        if data_format and data_format not in ["xml", "json", "html"]:
            raise exceptions.WrongParameters("The supported formats are xml, json or html!")
        LogsCall.__validate_datetime_param("start", start_time)
        LogsCall.__validate_datetime_param("end", end_time)

    @staticmethod
    def __validate_datetime_param(param_name: str, param_value: str):
        try:
            if param_value:
                parser.parse(param_value)
        except ValueError:
            raise exceptions.WrongParameters(f"The {param_name} parameter is not a dateTime value!")

    @staticmethod
    def __reformat_datetime_param(datetime_param: str):
        if datetime_param:
            return parser.parse(datetime_param).strftime("%Y-%m-%dT%H:%M:%S")
        else:
            return datetime_param
