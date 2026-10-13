"""Custom expressions for evaluator tests that need literal XQuery constructs."""

from mlclient.xquery import XqyExpression


class StaticExpression(XqyExpression):
    """Render fixed test-owned XQuery, never runtime input or XPath validation."""

    def __init__(self, source: str):
        self.source = source

    def render(self, _ctx):
        return f"({self.source})"
