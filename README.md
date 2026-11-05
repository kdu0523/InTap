# InTap

InTap is an internal AI engineering system that learns how a company's developers implement, review, and maintain software. It combines repository conventions, historical changes, PR discussions, and Jira work context into evidence-backed engineering profiles. Those profiles will guide a coding agent toward changes that fit the company's codebase and delivery practices.

The goal is to automate an increasing share of well-defined engineering work while measuring correctness, review effort, delivery cost, and business outcomes. Historical artifacts reveal observable decisions and working patterns; they do not reconstruct an engineer's private thoughts or establish that an agent can replace their full role.

## Current foundation

| Available now | Designed for later implementation |
| --- | --- |
| Offline Python source profiler with file, line, and content-hash evidence | GitHub PR/diff and Jira ingestion connectors |
| Explicit company rules and a task-context preparation CLI | Contextual profiles for company, repository, team, and individual developer |
| Versioned JSON Schema for ingestion events and a feature catalog | Model-based feature extraction and coding-agent adapters |
| Synthetic Git, PR comment, and Jira payloads; schema validation | Isolated patch execution, authenticated verification, and review workflow |
| Verification gate policy, automated tests, and GitHub Actions | Historical replay evaluation, pilot dashboard, and business impact measurement |

The current pipeline prepares context. It does not call a model, generate patches, execute company code, or deploy changes. Advanced telemetry examples are synthetic, not computed measurements.

## Quick start

Requires Python 3.11+ and `make`. The source-profile demo has no third-party runtime dependencies and makes no network requests.

```sh
make demo
make test
```

The demo reads only `examples/company_repo/` through `intap.toml`, then writes:

- `.intap/profile.json`: descriptive coding-pattern frequencies and source references.
- `.intap/run.json`: task, company rules, profile evidence, and proposed workflow.

For an installed CLI and full ingestion-contract validation:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
intap validate-ingestion --payload examples/ingestion/git-diff.json
intap profile --output .intap/profile.json
intap prepare --profile .intap/profile.json --task examples/task.json --output .intap/run.json
```

Schema and feature-catalog paths default to `schemas/` in the current directory. Use `--schema` and `--catalog` when running elsewhere. The package includes the CLI; the repository contains these contracts and fixtures.

## Project layout

```text
InTap/
├── src/intap/              # Domain contracts, local profiling, agent interfaces, CLI
├── schemas/                # Ingestion JSON Schema and feature definitions
├── examples/
│   ├── company_repo/       # Synthetic source code
│   ├── ingestion/          # Valid Git, PR comment, and Jira event fixtures
│   └── task.json           # Sample engineering task
├── tests/                  # Pipeline and ingestion-contract tests
├── docs/                   # Product, architecture, telemetry, and roadmap
├── .github/workflows/      # CI
├── intap.toml              # Demo source scope and company rules
├── Makefile
└── pyproject.toml
```

## Design documents

- [Ingestion schema and mathematical representation](docs/ingestion-schema.md)
- [Product scope and pilot outcomes](docs/product.md)
- [Architecture and trust boundaries](docs/architecture.md)
- [Implementation roadmap](docs/roadmap.md)
- [Contributing](CONTRIBUTING.md)

For a real company pilot, create an approved local configuration and store private artifacts and generated profiles outside tracked files. The local scanner excludes hidden directories, symlinks, and common dependency/build folders; it does not interpret `.gitignore` and is not an isolation boundary. Inspect the configured scope before running it. No company repository has been connected yet.
