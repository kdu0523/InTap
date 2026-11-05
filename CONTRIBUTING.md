# Contributing

Use Python 3.11+ and run `make test` before submitting changes. Install `.[dev]` to run ingestion JSON Schema checks; CI requires that extra. Run `make demo` when changing profiling or task preparation.

Keep feature definitions, extraction versions, evidence links, and missing-value semantics explicit. Add a regression test for changed behavior. Separate observed source facts from model-derived labels and from approved company policy.

Use synthetic data in committed examples and tests. Keep imported company artifacts, credentials, and generated profiles in ignored local storage. Do not enable real ingestion, model calls, or execution as a side effect of imports or tests.

Schema changes need a version decision, updated valid and invalid examples, and compatibility notes. The initial contract is pre-production and may evolve; once consumers depend on a version, introduce a migration rather than silently changing its meaning.
