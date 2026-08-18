# ceynex-contracts

The frozen interface surface of [CeyNex](https://github.com/CeyNex-AI) — a
multi-agent decision intelligence platform for Sri Lanka's national export
economy. Group 07, Project P16, CS3501, University of Moratuwa.

This package exists so that three people can build in parallel without waiting
on each other. It holds the shapes everyone codes against and nothing else: no
business logic, no I/O, no dependencies beyond pandas and typing-extensions.

## Install

```bash
pip install "ceynex-contracts @ git+ssh://git@github.com/CeyNex-AI/ceynex-contracts.git"
# or, working locally alongside a checkout:
pip install -e ../ceynex-contracts
```

## What it gives you

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

The database schemas ship as package data and are applied programmatically, so
the same code path works against a local container and the deployed VM:

```python
from importlib.resources import files

sql    = (files("ceynex.contracts") / "schema" / "schema.sql").read_text()
cypher = (files("ceynex.contracts") / "schema" / "schema.cypher").read_text()
```

## `ceynex` is a namespace package

This distribution supplies `ceynex.contracts`; `ceynex-core` supplies
`ceynex.data`, `ceynex.kg`, `ceynex.agents`, `ceynex.orchestrator` and the rest.
Neither ships a `ceynex/__init__.py`. Adding one back shadows the other
distribution and breaks every import in the team's code.

## The rule

**Nothing here changes without all three members agreeing.** That is the whole
point of the package being separate — a contract change is a pull request with
three reviewers, not a quiet commit at 23:00. See
[ceynex/contracts/CLAUDE.md](ceynex/contracts/CLAUDE.md) for what is most
likely to be broken by accident.
