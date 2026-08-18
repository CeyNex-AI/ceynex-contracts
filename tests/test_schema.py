"""The schemas ship as package data, so these tests are what notices if they stop shipping.

SRS 3.10.1-3.10.2 (database schemas). `ceynex.data.bootstrap` and
`ceynex.kg.load` over in ceynex-core read these through importlib.resources; a
packaging change that drops them turns into a confusing runtime failure on a VM
rather than a red test here.
"""

import re
from importlib.resources import files
from pathlib import Path

import pytest

SCHEMA = files("ceynex.contracts") / "schema"

# Team overview 4.3, SAD 9 — "do not improvise". A loader needing a label
# outside this set is a contract change, not a commit.
NODE_LABELS = {
    "Commodity",
    "ApparelCategory",
    "Country",
    "District",
    "HSCode",
    "TradeAgreement",
}

FACT_TABLES = {"dim_country", "dim_hs", "fact_trade", "dq_flag", "ingest_run"}


def read(name: str) -> str:
    return (SCHEMA / name).read_text(encoding="utf-8")


def test_both_schemas_are_installed_package_data():
    """Reachable through the package, not just present in a source checkout."""
    for name in ("schema.sql", "schema.cypher"):
        assert (SCHEMA / name).is_file(), f"{name} did not ship with the package"
        assert read(name).strip(), f"{name} shipped empty"


def test_sql_declares_every_contracted_table():
    sql = read("schema.sql").lower()
    declared = set(re.findall(r"create table(?:\s+if not exists)?\s+(\w+)", sql))
    assert FACT_TABLES <= declared, f"missing: {FACT_TABLES - declared}"


def test_fact_trade_carries_both_country_coding_standards():
    """SRS 3.6.1: neither M49 nor ISO-3 may be treated as authoritative alone."""
    sql = read("schema.sql").lower()
    for column in ("reporter_iso3", "reporter_m49", "partner_iso3", "partner_m49"):
        assert column in sql, f"fact_trade lost {column}"


def test_fact_trade_keeps_its_idempotency_key():
    """The writer upserts on source_hash; losing it silently duplicates rows."""
    assert "source_hash" in read("schema.sql").lower()


def test_cypher_constrains_exactly_the_contracted_labels():
    cypher = read("schema.cypher")
    constrained = set(re.findall(r"FOR\s+\(\w+:(\w+)\)\s+REQUIRE", cypher))
    assert constrained == NODE_LABELS, (
        f"unexpected: {constrained - NODE_LABELS}, missing: {NODE_LABELS - constrained}"
    )


def test_every_cypher_statement_is_idempotent():
    """Three members re-run their loaders against one instance; re-applying must be free."""
    cypher = read("schema.cypher")
    statements = [
        line
        for line in cypher.splitlines()
        if re.match(r"\s*CREATE\s+(CONSTRAINT|INDEX)", line, re.I)
    ]
    assert statements, "no constraints or indexes found at all"
    for statement in statements:
        assert "IF NOT EXISTS" in statement.upper(), f"not idempotent: {statement.strip()}"


def test_exports_to_year_is_indexed():
    """Every Export Analytics query filters EXPORTS_TO by year (SRS 3.1.6)."""
    assert re.search(r"\[r:EXPORTS_TO\]-\(\)\s*ON\s*\(r\.year\)", read("schema.cypher"))


def test_ceynex_stays_a_namespace_package():
    """An `__init__.py` here shadows ceynex-core and breaks every teammate's imports."""
    import ceynex.contracts

    package_root = Path(ceynex.contracts.__file__).parent.parent
    offender = package_root / "__init__.py"
    if offender.exists():
        pytest.fail(f"delete {offender} — ceynex must stay an implicit namespace package")
