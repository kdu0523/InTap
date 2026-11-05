# Ingestion contract and developer behavior features

The canonical contract is [ingestion-event.schema.json](../schemas/ingestion-event.schema.json), using [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12). Definitions and value constraints are in [feature-catalog.json](../schemas/feature-catalog.json). Three [synthetic events](../examples/ingestion/) demonstrate Git diffs, PR comments, and Jira issues. Artifact URIs, hashes, and classifier results in these fixtures are illustrative; they do not resolve to real company data.

## Event envelope

Store one event per source artifact revision, with a typed `payload` and an independent `features` array. Keep raw source artifacts in restricted storage and reference them by URI and content hash. Do not flatten an engineer's history into one mutable personality document.

| Field | Meaning |
| --- | --- |
| `schema_version`, `feature_catalog_version` | Version the shape and mathematical feature definitions independently. |
| `event_id` | Stable ID for this normalized revision; a connector should derive it deterministically for idempotent retries. |
| `tenant_id` | Company boundary. The future server must verify this against authenticated context. |
| `subject` | Pseudonymous developer ID, role in this artifact, identity-map version, attribution method, optional calibrated attribution confidence. |
| `event_type` | `git.diff`, `pr.comment`, or `jira.issue`; determines payload and source-system shape. |
| `occurred_at` | Time of the represented source revision or action, not necessarily the artifact's original creation time. |
| `available_at` | Earliest time this exact revision was observed and usable by InTap; never infer historical availability from creation time alone. |
| `ingested_at` | Time this normalized revision entered InTap. |
| `source` | Provider, instance, stable object ID, revision, connector version, and restricted raw-artifact reference. |
| `processing` | Pipeline version and hash of the complete extraction configuration, allowing a source revision to be reprocessed without overwriting its previous derived representation. |
| `context` | Repository, team, project, programming language, natural language, frameworks, task type, and task-label origin. Unknown context remains explicit. |
| `quality` | Synthetic/bot/bulk-change flags, source completeness, and declared pairing or AI assistance; unknown is not false. |
| `retention` | Classification, redaction version, policy reference, and expiry. Enforcement belongs in storage and lifecycle services. |
| `links` | Explicit or inferred PR–commit–ticket relationships with method, availability time, and optional calibrated confidence. |
| `features` | Measured or inferred values, units, versions, methods, evidence pointers, and availability times. |

The raw source-revision key is `(tenant_id, source.system, source.instance_id, source.object_id, source.revision)`. Deduplicate raw deliveries on that key. The normalized-event key additionally includes schema/catalog versions, `processing.pipeline_version`, and `processing.configuration_sha256`; derive a stable event ID from that complete key. A new pipeline/configuration produces a new immutable event, while retrying the same processing key must be idempotent. A feature key additionally includes name, definition version, entity, phase, and extractor/configuration identity. The validator rejects duplicate name/entity/phase measurements within a single event. Alternative extractor outputs require separate processing configurations rather than ambiguous duplicates. The future store must enforce these uniqueness keys; the local validator checks one event at a time.

## Source-specific payloads

**Git diffs.** Capture repository ID, exact base/head commit IDs, verified author IDs, committer ID, and per-file path/rename state, language, additions, deletions, test/generated/vendor flags, diff reference, and `before_blob`/`after_blob` references. An added file has no before blob; a deleted file has no after blob. Compute metrics on complete blobs rather than partial patch context. Match the same symbol across revisions before calculating deltas; explicitly mark added/deleted or unmatchable symbols as unavailable for comparable deltas. Keep symbol-matching method and configuration in extraction provenance.

**PR comments.** Preserve author role, comment kind, thread/reply relationships, created/updated timestamps, resolution state, body reference, and inline anchor where present. Anchors include path, line, side, commit ID, and original commit ID; these are distinct source concepts in [GitHub's review-comment API](https://docs.github.com/en/rest/pulls/comments?apiVersion=2022-11-28). The raw artifact preserves full hunks and multiline/file-level anchors that are not normalized in v1. Conversation comments and review summaries need their own connector endpoints, not just inline-review-comment ingestion. Resolution is an observed thread state, not proof that a suggestion was correct or adopted.

**Jira issues.** Preserve issue/project IDs, type, status, priority, assignee/reporter references, creation/update times, description reference, and individual field-change records with actor and timestamp. Jira v3 descriptions/comments can use Atlassian Document Format; preserve that source media type before deriving text. Use paginated [issue changelogs](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/) for historical state. An issue being assigned to a developer does not establish that they authored its requirements or performed every transition. V1 models issue snapshots and field changes; Jira comments need a future typed event rather than being silently mixed into the issue description.

## Telemetry catalog

| Family | Proposed measurements | Interpretation and controls |
| --- | --- | --- |
| Code structure | Cyclomatic/cognitive complexity before, after, and delta; nesting depth; function length; logical lines | Per matched callable and language-specific analyzer. Complexity is structural, not a measure of intelligence. |
| Coding conventions | Naming ratios, type-annotation coverage, docstring coverage, comment-to-code ratio | Store numerator/denominator and scope. Separate comments, docstrings, and executable lines. |
| Change strategy | Added/deleted lines, churn, test-to-production churn, post-review rework | Exclude generated/vendor code; normalize by task size. Large changes may be required by the task. |
| Architecture | Patterns introduced/retained, boundary-crossing edges, dependency changes, error-handling strategy | Evidence per component; version the taxonomy and distinguish deterministic detection from model labels. |
| Review behavior | Review topic, request/question/suggestion intent, rationale present, feedback adoption | Bind comments to subsequent changes. Adoption needs explicit adjudication; temporal proximity alone is insufficient. |
| Language | Optional comment-level sentiment, hedging ratio, question/request distribution | Remove quoted text and code blocks; retain language/model/prompt versions and calibration results. Tone is not engineering ability or a stable personality trait. |
| Delivery process | Review rounds, review/response latency, ticket requirement churn, dependency/blocker history | Elapsed time is affected by queues and schedules; it is not active work time. V1 preserves status history; richer blocker and PR lifecycle events are an extension. |
| Outcomes | Verified acceptance, regression/revert labels, reviewer effort, accepted-task cost | Treat later outcomes as evaluation labels, not features available before the original task. V1 includes revert/regression definitions; CI and cost evidence need additional source adapters. |

All catalog extractors are planned. The separate local Python demo currently computes only snake-case function frequency, return-annotation frequency, function-docstring frequency, and async-function frequency. It does not emit the advanced telemetry above.

## Measurement representation

For example, this is one feature object from the valid Git event fixture:

```json
{
  "name": "code.comment_to_code_ratio",
  "definition_version": "1.0.0",
  "entity_id": "orders.py::calculate_total",
  "scope": {
    "kind": "callable",
    "path": "orders.py",
    "symbol_id": "orders.calculate_total",
    "start_line": 4,
    "end_line": 12
  },
  "phase": "after",
  "value": 0.2,
  "unit": "ratio",
  "status": "derived",
  "method": "static_analysis",
  "extractor": {
    "name": "synthetic-fixture",
    "version": "1.0.0",
    "config_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
  },
  "evidence": ["/payload/files/0/after_blob"],
  "available_at": "2026-11-04T15:02:00Z",
  "numerator": 4,
  "denominator": 20
}
```

Evidence pointers resolve within the enclosing event to source references. `scope` records the entity kind and, for source-level metrics, the matched symbol and source span. Before and after measurements use their corresponding blob and span. A delta points to both blobs; its scope identifies the matched entity. A file-level pointer alone does not prove a symbol-level finding.

Use `status: "unavailable"`, `value: null`, and a `missing_reason` for unparseable, unsupported, redacted, unmatchable, or denominator-zero observations. Zero means a measured zero. Do not substitute it for missing data. `confidence` is optional and requires `confidence_calibration_version` when present; a model's self-reported certainty is not calibrated confidence.

## Mathematical definitions

For a matched callable, `delta_cc = cc_after - cc_before`. A negative value indicates reduced structural complexity under the same analyzer/configuration. A new or deleted callable has no comparable delta. Radon's Python definition counts decisions plus one; its AST rules are documented in [Introduction to Code Metrics](https://radon.readthedocs.io/en/latest/intro.html). Different analyzers/languages need distinct definitions and cannot be mixed casually.

Define `comment_to_code_ratio = comment_bearing_physical_lines / physical_code_lines`, excluding blanks and docstrings. An inline comment can make a line count in both categories. The ratio may exceed one. Retain both counts; denominator zero means unavailable. Do not use raw LOC or this ratio as a quality score.

For each measurement `x_i`, create a context-adjusted feature using only the training cohort for the matching repository/language/task family:

```text
z_i = (g(x_i) - median_cohort(g(x))) / max(1.4826 * MAD_cohort(g(x)), epsilon)
```

Use `g(x) = log1p(x)` for nonnegative skewed counts/latencies and the identity or a documented signed transform for signed deltas. Require a minimum cohort size and a predefined fallback hierarchy; record normalization version and missingness masks. Keep category probabilities or frequency distributions rather than averaging arbitrary category IDs.

For developer `d`, context `c`, and cutoff `T`, summarize eligible measurements using provenance quality and time decay:

```text
w_i = attribution_weight_i * extraction_quality_weight_i * exp(-(T - t_i) / tau)
mu_d,c = sum(w_i * z_i) / sum(w_i)
n_eff = sum(w_i)^2 / sum(w_i^2)
profile_d,c = shrink(n_eff, k) * mu_d,c + (1 - shrink(n_eff, k)) * mu_team,c
shrink(n_eff, k) = n_eff / (n_eff + k)
```

These are proposed modeling choices, not universal truths or implemented estimators. Quality weights need a defined, validated meaning; use conservative fixed inclusion rules where calibrated weights are unavailable. Estimate uncertainty by resampling independent task groups, not correlated comments from the same PR. Require sufficient independent tasks before serving an individual preference. Preserve distributions, support counts, drift, and uncertainty alongside means.

The resulting representation is a contextual behavioral profile, not a unique biometric fingerprint or a recovered thought process. Model reasoning-related behavior through explicit rationale, alternatives discussed, requirement clarifications, and observed revisions. Avoid a single scalar developer score. Store embeddings as separately versioned derived artifacts with model ID, dimensions, input hash, and deletion lineage; do not mix vectors from incompatible embedding models.

## Temporal integrity and validation

Validate the Draft 2020-12 shape with format checking enabled, then apply semantic checks. The supplied validator checks timestamp ordering, future-known links, feature availability, known feature definitions, units and value ranges, evidence-pointer resolution, duplicate measurements, ratio arithmetic, and matched before/after deltas. Schema validation alone cannot establish source authenticity, correct attribution, extraction correctness, or authorization.

At evaluation cutoff `T`, include only events and features with `available_at <= T`, using the exact revision known then. Future review outcomes, final Jira resolutions, merged diffs, and later comment edits must not leak into the prediction context. Historical backfills observed today do not prove that InTap knew those revisions in the past. Replay evaluation requires reconstructable revision history and an explicit historical-availability policy. Unknown or censored outcomes remain unavailable until the observation horizon has elapsed.

```sh
intap validate-ingestion --payload examples/ingestion/git-diff.json
intap validate-ingestion --payload examples/ingestion/pr-comment.json
intap validate-ingestion --payload examples/ingestion/jira-issue.json
```
