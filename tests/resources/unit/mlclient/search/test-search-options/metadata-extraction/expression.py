from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.ExtractMetadata(
            [
                o.MetadataQName(s.Element("title", "https://example.com/docs")),
                o.MetadataQName(s.Element("item"), s.Attribute("code")),
                s.JsonProperty("title"),
                s.JsonProperty("author"),
                o.ConstraintValue("tag"),
            ],
        ),
    )
