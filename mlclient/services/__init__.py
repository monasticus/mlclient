"""The ML Services package.

High-level services providing parsed results from MarkLogic operations.
"""

from .documents import DocumentsService
from .eval import LOCAL_NS, EvalService
from .logs import LogsService, LogType

__all__ = [
    "LOCAL_NS",
    "DocumentsService",
    "EvalService",
    "LogType",
    "LogsService",
]
