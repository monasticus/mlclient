"""Search API query contracts, models and factory modules.

Use sq for structured query factories and opt for option factories. Their
immutable model classes belong to structured and options respectively. This
package does not import the XQuery compiler or CTS query implementations.
"""

from mlclient.search import opt, sq
from mlclient.search.base import QueryComponent, SearchQuery

__all__ = ["QueryComponent", "SearchQuery", "opt", "sq"]
