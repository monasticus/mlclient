"""Reconstruct column queries in an isolated database with a real TDE view."""

import json
import os
from uuid import uuid4
from xml.etree.ElementTree import fromstring, tostring

import pytest

from mlclient import MLClient
from mlclient.xquery import cts
from mlclient.http import HTTPConfig

pytestmark = pytest.mark.ml_access


class TestCtsColumnSerialization:
    @pytest.fixture(scope="class")
    @staticmethod
    def database():
        name = f"mlclient-column-query-{uuid4().hex}"
        created = []
        with MLClient(
            port=int(os.environ.get("MLCLIENT_CTS_PORT", "8000")),
            manage_config=HTTPConfig.resolve(
                port=int(os.environ.get("MLCLIENT_CTS_MANAGE_PORT", "8002")),
            ),
        ) as ml:
            try:
                for db in (name + "-schemas", name):
                    ml.manage.databases.create({"database-name": db}).raise_for_status()
                    created.append(db)
                    ml.manage.forests.create(
                        {
                            "forest-name": db,
                            "host": ml.eval.xquery("xdmp:host-name(xdmp:host())"),
                            "database": db,
                        },
                    ).raise_for_status()
                ml.manage.databases.put_properties(
                    name,
                    {
                        "schema-database": name + "-schemas",
                        "triple-index": True,
                        "uri-lexicon": True,
                    },
                ).raise_for_status()
                ml.eval.xquery(
                    'import module namespace tde="http://marklogic.com/xdmp/tde" '
                    'at "/MarkLogic/tde.xqy";\n'
                    'tde:template-insert("/report-template.xml", '
                    '<template xmlns="http://marklogic.com/xdmp/tde">'
                    "<context>/report</context><rows><row><schema-name>reports"
                    "</schema-name><view-name>items</view-name><columns><column>"
                    "<name>price</name><scalar-type>int</scalar-type><val>price</val>"
                    "</column></columns></row></rows></template>)",
                    database=name,
                )
                ml.eval.xquery(
                    'xdmp:document-insert("/report.xml", '
                    '<report><price>2</price></report>)',
                    database=name,
                )
                yield ml, name
            finally:
                for db in reversed(created):
                    ml.manage.databases.delete(
                        db, forest_delete="data",
                    ).raise_for_status()

    def test_column_json_and_xml_find_the_native_results(self, database):
        ml, name = database
        query = cts.column_range_query("reports", "items", "price", 2)
        code, variables = query.compile()
        prolog, body = code.rsplit("\n", 1)
        native_xml = ml.eval.xquery(
            prolog + "\nxdmp:quote(<a>{" + body + "}</a>/*)",
            variables=variables,
            database=name,
        )
        predicate = fromstring(native_xml).find("{http://marklogic.com/cts}predicate")
        described = query.with_column_id(int(predicate.get("columnID")))
        variables.update(
            json=json.dumps(described.to_json()),
            xml=tostring(described.to_xml(), encoding="unicode"),
        )
        results = ml.eval.xquery(
            prolog
            + "\ndeclare variable $json external;declare variable $xml external;\n"
            "let $native := " + body + "\nreturn array-node {\n"
            "for $query in ($native, cts:query(xdmp:unquote($json)/node()), "
            "cts:query(xdmp:unquote($xml)/*)) return array-node {"
            "cts:uris((), (), $query)}}",
            variables=variables,
            database=name,
        )
        assert results == [["/report.xml"], ["/report.xml"], ["/report.xml"]]
