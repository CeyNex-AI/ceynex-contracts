# ceynex-contracts

The frozen interfaces of **CeyNex**, a multi-agent decision intelligence platform for Sri Lanka's export economy. This package defines the shapes the rest of the system codes against:

- the agent state that flows through the LangGraph orchestrator;
- the evidence and forecast records every answer carries;
- the protocols that data connectors and forecasting models implement;
- the PostgreSQL and Neo4j schemas.

It holds no business logic and no I/O. Its only runtime dependencies are pandas and typing-extensions.

Group 07, Project P16, CS3501 Data Science and Engineering Project, University of Moratuwa.

## Why a separate package

Three people built CeyNex in parallel: agriculture, core systems, and apparel plus the front end. Putting the shared shapes in their own repository meant each of us could build against a fixed interface without waiting on the others. It also means a change to an interface is a visible pull request, not a side effect of someone's feature branch.

**The rule: nothing in this repo changes unless all three members approve the pull request.**

## Where it fits

| Repo | Uses this package for |
|---|---|
| [`ceynex-core`](https://github.com/CeyNex-AI/ceynex-core) | Agents, orchestrator, connectors, models; `make db-init` and `make kg-load` apply the schemas from here |
| [`ceynex-infra`](https://github.com/CeyNex-AI/ceynex-infra) | The backend image installs it next to `ceynex-core` |
| [`trade-data-pipeline`](https://github.com/CeyNex-AI/trade-data-pipeline) | Indirectly, through `ceynex-core`'s retrieval schema |

## Install

```bash
# alongside a ceynex-core checkout (what `make install` in ceynex-core does)
pip install -e ../ceynex-contracts

# or straight from GitHub
pip install "ceynex-contracts @ git+https://github.com/CeyNex-AI/ceynex-contracts.git"
```

Requires Python 3.11 or later.

## What it provides

```python
from ceynex.contracts import (
    AgentState, AgentOutput, Evidence, ForecastPoint,   # the state contract
    ALL_AGENTS, DEFAULT_AGENT, AgentName, Sector,
    new_state, failed_output, merge_agent_outputs,      # helpers
    DataSourceConnector, SourceManifest,                # subclass for a connector
    ForecastModel,                                      # subclass for a model
    CrossValidatorProtocol, NullCrossValidator, DQFlag,
    KnowledgeGraphClientProtocol, LLMReasoningClientProtocol,
)
```

| File | Contents |
|---|---|
| `ceynex/contracts/state.py` | `AgentState` (the LangGraph state), `AgentOutput`, `AgentName`, `Sector`, the reducers that let parallel agents write to the same keys, and helpers `new_state`, `failed_output`, `merge_agent_outputs` |
| `ceynex/contracts/evidence.py` | `Evidence`: `source_id`, `claim`, `detail` (the literal Cypher or SQL that produced the claim), and optional `period` and `url`. This is what the evidence panel shows. |
| `ceynex/contracts/forecast.py` | `ForecastPoint`: `period`, `point`, the required `lower` / `upper` interval bounds, and `unit` |
| `ceynex/contracts/protocols.py` | `DataSourceConnector` + `SourceManifest`, `ForecastModel`, `CrossValidatorProtocol` + `DQFlag` + `NullCrossValidator`, and the protocols for the knowledge-graph client and the LLM client |
| `ceynex/contracts/schema/schema.sql` | PostgreSQL schema |
| `ceynex/contracts/schema/schema.cypher` | Neo4j constraints and indexes |

### PostgreSQL schema

| Table | Holds |
|---|---|
| `dim_country` | Countries with ISO 3166 alpha-3 and UN M49 codes |
| `dim_hs` | Harmonised System codes and descriptions |
| `fact_trade` | Every trade observation: source, sector, item, HS code, reporter and partner (ISO3 and M49), period and frequency, volume, value in USD, price, FX rate and source hash. A unique key over source, item, HS code, reporter, partner, period and frequency makes re-ingesting idempotent. Production holds 13,132 rows from 8 sources. |
| `fact_provenance` | For curated workbook facts: the publisher, workbook file and its SHA-256, sheet and row each `fact_trade` row came from |
| `dq_flag` | Data-quality flags when two sources disagree on the same observation: both values, the percentage difference, severity (minor, material, severe) and whether it is resolved |
| `ingest_run` | One row per connector run: source, start and finish, status, rows written and any error |

### Neo4j schema

The schema defines uniqueness constraints on `Country` (iso3 and m49), `HSCode`, `Commodity`, `ApparelCategory`, `District`, `TradeAgreement` and `PolicyDocument`. It also defines indexes on country name, HS description, policy-document iso3, the year on `EXPORTS_TO` and the start year on `COVERED_BY`.

Both schemas ship as package data, so the same code applies them to a local container and to production:

```python
from importlib.resources import files

sql    = (files("ceynex.contracts") / "schema" / "schema.sql").read_text()
cypher = (files("ceynex.contracts") / "schema" / "schema.cypher").read_text()
```

## Things that are easy to break

1. **`ceynex` is a namespace package.** This distribution supplies `ceynex.contracts`, and `ceynex-core` supplies `ceynex.data`, `ceynex.kg`, `ceynex.agents` and the rest. Neither repo ships a `ceynex/__init__.py`. Adding one shadows the other distribution and breaks every import.
2. **The `Annotated[...]` reducers on `agent_outputs`, `errors` and `degraded` are load-bearing.** Cross-sector questions send work to two or three agents in parallel. Without a reducer, LangGraph raises `InvalidUpdateError` as soon as two parallel branches write the same key. `tests/test_state.py` guards this.
3. **`ForecastPoint.lower` and `.upper` are required.** The SRS forbids presenting a forecast as a bare number. A model that cannot produce an interval gets one by residual bootstrap. It is not allowed to leave the fields out.
4. **pandas is a real runtime import.** `DataSourceConnector.fetch()` is annotated as returning `pd.DataFrame`, so moving pandas to a type-checking-only import would itself be a contract change.

## Development

```bash
make install   # pip install -e ".[dev]" + pre-commit
make test      # pytest: state shape, reducers, schema packaging
make lint      # ruff
make fmt
```

CI (`.github/workflows/ci.yml`) runs ruff and pytest on every push and pull request.

## Changing a contract

1. Open an issue or a short proposal describing the change and which repos it touches. [`docs/CONTRACT_PROPOSAL_POLICY_DOCUMENT.md`](https://github.com/CeyNex-AI/ceynex-core/blob/main/docs/CONTRACT_PROPOSAL_POLICY_DOCUMENT.md) in ceynex-core is an example.
2. Open a pull request here with the change and its tests.
3. Get approval from all three members, then merge.
4. Update `ceynex-core` (and redeploy) in step with it. New tables and constraints use `IF NOT EXISTS`, so re-running `make db-init` and `make kg-load` is safe on an existing database.

## History

| Change | PR |
|---|---|
| Agent state, evidence, forecast and protocol contracts; PostgreSQL and Neo4j schemas as package data | initial |
| CI: lint and test workflow | #2 |
| `PolicyDocument` constraint and iso3 index (policy retrieval) | #3 |
| `fact_provenance` table for curated agriculture facts | #4 |

## Team

Senindu Dinapura (230151T), Thisen Ekanayake (230170B), Dhinanjaya Fernando (230181J). Supervisor: Dr. Chathuranga Hettiarachchi, University of Moratuwa.
