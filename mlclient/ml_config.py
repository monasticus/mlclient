"""The ML Configuration module.

This module contains an API for MarkLogic configuration.
It exports the following classes:
    * MLConfiguration
        A class representing MarkLogic configuration.
    * MLAppServerConfiguration
        A class representing MarkLogic App Server configuration.
    * AuthMethod
        An enumeration class representing authorization methods.
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel, Field


class AuthMethod(Enum):
    """An enumeration class representing authorization methods."""

    BASIC = "basic"
    DIGEST = "digest"


class MLConfiguration(BaseModel):
    """A class representing MarkLogic configuration.

    Attributes
    ----------
    app_name : str
        An application name
    protocol : str
        An HTTP protocol
    host : str
        A hostname
    username : str
        An username
    password : str
        A password
    app_servers : List[MLAppServerConfiguration]
        App Servers configurations' list
    """

    app_name: str = Field(
        alias="app-name")
    protocol: str = "http"
    host: str = "localhost"
    username: str = "admin"
    password: str = "admin"
    app_servers: List[MLAppServerConfiguration] = Field(
        alias="app-servers",
        default=[])

    @classmethod
    def from_file(
            cls,
            file_path: str,
    ) -> MLConfiguration:
        """Instantiate MLConfiguration from a file.

        Parameters
        ----------
        file_path : str
            A source configuration file

        Returns
        -------
        MLConfiguration
            An MLConfiguration instance
        """
        with Path(file_path).open() as config_file:
            source_config = yaml.safe_load(config_file.read())
            return MLConfiguration(**source_config)


class MLAppServerConfiguration(BaseModel):
    """A class representing MarkLogic App Server configuration.

    Attributes
    ----------
    identifier : str
        A unique identifier of the App Server
    port : int
        A port number
    auth : AuthMethod
        An authorization method
    """

    identifier: str = Field(
        alias="id")
    port: int
    auth: AuthMethod = AuthMethod.DIGEST
