"""The ML Logs Resource Call module.

It exports 1 class:
    * LogsCall
        A GET request to retrieve logs.
"""
from __future__ import annotations

from dateutil import parser

from mlclient import exceptions, utils
from mlclient.calls import ResourceCall


class LogsCall(ResourceCall):
    """A GET request to retrieve logs.

    A ResourceCall implementation representing a single GET request
    to the /manage/v2/logs REST Resource.

    Returns the content of server log files.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/logs
    """

    _ENDPOINT: str = "/manage/v2/logs"

    _FORMAT_PARAM: str = "format"
    _FILENAME_PARAM: str = "filename"
    _HOST_PARAM: str = "host"
    _START_PARAM: str = "start"
    _END_PARAM: str = "end"
    _REGEX_PARAM: str = "regex"

    def __init__(
            self,
            filename: str,
            data_format: str = "html",
            host: str | None = None,
            start_time: str | None = None,
            end_time: str | None = None,
            regex: str | None = None,
    ):
        """Initialize LogsCall instance.

        Parameters
        ----------
        filename : str
            The log file to be returned.
        data_format : str
            The format of the data in the log file. The supported formats are xml, json
            or html.
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
        self._validate_params(data_format, start_time, end_time)

        super().__init__(accept=utils.get_accept_header_for_format(data_format))
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._FILENAME_PARAM, filename)
        self.add_param(self._HOST_PARAM, host)
        self.add_param(self._START_PARAM,
                       self._reformat_datetime_param(start_time))
        self.add_param(self._END_PARAM,
                       self._reformat_datetime_param(end_time))
        self.add_param(self._REGEX_PARAM, regex)

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Logs call.

        Returns
        -------
        str
            A Logs call endpoint
        """
        return self._ENDPOINT

    @classmethod
    def _validate_params(
            cls,
            data_format: str,
            start_time: str,
            end_time: str,
    ):
        if data_format and data_format not in ["xml", "json", "html"]:
            msg = "The supported formats are xml, json or html!"
            raise exceptions.WrongParametersError(msg)
        cls._validate_datetime_param("start", start_time)
        cls._validate_datetime_param("end", end_time)

    @staticmethod
    def _validate_datetime_param(
            param_name: str,
            param_value: str,
    ):
        try:
            if param_value:
                parser.parse(param_value)
        except ValueError:
            msg = f"The {param_name} parameter is not a dateTime value!"
            raise exceptions.WrongParametersError(msg) from ValueError

    @staticmethod
    def _reformat_datetime_param(
            datetime_param: str,
    ):
        if datetime_param:
            return parser.parse(datetime_param).strftime("%Y-%m-%dT%H:%M:%S")
        return datetime_param
