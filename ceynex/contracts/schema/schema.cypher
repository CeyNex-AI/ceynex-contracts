// CeyNex knowledge graph — constraints and indexes.  FROZEN CONTRACT.
//
// SRS 3.10.1 (graph database schema), SAD §5.2 Knowledge Graph package and
// §9, team overview §4.3.  Six node types, four relationship types; the SAD
// says "do not improvise", so a loader that needs a new label or edge type
// raises a contract change rather than adding one.
//
// Applied by `ceynex.kg.load` (see also `make kg-load`), never by hand and
// never through an initdb-style mount — the same code path has to work
// against a local container and against the shared VM.
//
// Every statement is IF NOT EXISTS: three members run their loaders against
// the same instance and this file is re-applied on every load.

// --- Node keys ------------------------------------------------------------
// Country carries both M49 and ISO 3166-1 alpha-3 (SRS 3.6.1: neither coding
// standard is authoritative on its own).  iso3 is the graph key because it is
// what the agents' Cypher joins on; m49 gets its own uniqueness constraint so
// a crosswalk bug surfaces as a write failure rather than a duplicate node.
CREATE CONSTRAINT country_iso3 IF NOT EXISTS
  FOR (c:Country) REQUIRE c.iso3 IS UNIQUE;

CREATE CONSTRAINT country_m49 IF NOT EXISTS
  FOR (c:Country) REQUIRE c.m49 IS UNIQUE;

CREATE CONSTRAINT hscode_code IF NOT EXISTS
  FOR (h:HSCode) REQUIRE h.code IS UNIQUE;

CREATE CONSTRAINT commodity_name IF NOT EXISTS
  FOR (c:Commodity) REQUIRE c.name IS UNIQUE;

CREATE CONSTRAINT apparel_category_name IF NOT EXISTS
  FOR (a:ApparelCategory) REQUIRE a.name IS UNIQUE;

CREATE CONSTRAINT district_name IF NOT EXISTS
  FOR (d:District) REQUIRE d.name IS UNIQUE;

CREATE CONSTRAINT trade_agreement_name IF NOT EXISTS
  FOR (t:TradeAgreement) REQUIRE t.name IS UNIQUE;

// --- Lookup indexes -------------------------------------------------------
// Country.name and HSCode.description back the "which country / what is this
// code" lookups the router does before it can parameterize a query.
CREATE INDEX country_name IF NOT EXISTS
  FOR (c:Country) ON (c.name);

CREATE INDEX hscode_description IF NOT EXISTS
  FOR (h:HSCode) ON (h.description);

// --- Relationship indexes -------------------------------------------------
// Every Export Analytics query filters EXPORTS_TO by year: cagr() bounds a
// range, market_share() and top_partners() pin a single year.  Without this
// index each one is a full relationship scan.
CREATE INDEX exports_to_year IF NOT EXISTS
  FOR ()-[r:EXPORTS_TO]-() ON (r.year);

// agreement_coverage() (SRS 3.1.9, the GSP+ check) walks COVERED_BY and has to
// decide whether the agreement was in force in the period being simulated.
CREATE INDEX covered_by_from_year IF NOT EXISTS
  FOR ()-[r:COVERED_BY]-() ON (r.from_year);
