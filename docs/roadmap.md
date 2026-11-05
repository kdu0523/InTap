# Implementation roadmap

## Foundation — current

- Versioned ingestion contract, telemetry catalog, and synthetic source events.
- Offline local source profiling and grounded task-context preparation.
- Model and executor boundaries, verification policy, tests, and CI.

## 1. Read-only historical ingestion

Implement GitHub PR, review, conversation-comment, commit/diff, and Jira issue/changelog connectors. Preserve source revisions, pagination checkpoints, availability times, actor identities, and explicit cross-source links. Add company identity mapping, artifact storage, and scoped access controls.

Exit criterion: replaying a backfill produces no duplicate logical revisions, preserves evidence links, and passes tenant-isolation and deletion tests on an approved pilot dataset.

## 2. Feature extraction and contextual profiles

Implement language-specific syntax metrics, matched-symbol complexity deltas, review-intent labels, and explicit architectural-decision records. Validate model annotations against human-labeled samples before enabling them. Build company/repository baselines and developer residual profiles with uncertainty and minimum-support thresholds.

Exit criterion: feature extraction is reproducible, attribution errors can be corrected, and held-out annotations meet agreed quality thresholds. Sentiment remains optional and separate from engineering quality.

## 3. Patch-proposal agent and sandbox

Connect a model gateway to retrieved context. Generate patches in disposable checkouts, run independent task tests and existing regression checks, capture resource costs, and present evidence and verification results for review.

Exit criterion: the personalized agent improves an agreed task metric against the same-model baseline without exceeding the allowed regression, review-effort, or cost thresholds.

## 4. Internal pilot and selective automation

Add the internal API, review interface, authenticated run records, observability, and pilot reporting. Expand autonomy gradually by demonstrated task category. Track accepted-task economics and measured delivery outcomes; do not substitute style similarity for successful engineering work.
