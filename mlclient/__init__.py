"""Python clients for MarkLogic: direct connections and environment management."""

from ._client import AsyncMLClient, MLClient
from ._logging import register_fine_logging as _register_fine_logging
from ._manager import MLClientManager
from ._version import __version__

_register_fine_logging()

__all__ = ["AsyncMLClient", "MLClient", "MLClientManager", "__version__"]
