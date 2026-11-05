# Product foundation

## Problem and objective

Company-specific engineering knowledge is spread across code, pull requests, review conversations, tickets, and unwritten conventions. A generic coding agent can miss local architectural constraints, preferred abstractions, domain assumptions, and the rationale for previous changes.

InTap will turn approved engineering artifacts into retrievable, versioned evidence and use that evidence to implement bounded engineering tasks. The long-term objective is greater autonomous delivery with lower total engineering cost and better business throughput. Replacement of an entire engineering role is a hypothesis requiring substantially broader evidence than matching coding style.

## What the system learns

- Coding conventions: naming, typing, documentation, testing, error handling, and change granularity.
- Implementation choices: abstractions, dependency boundaries, design patterns, and recurring tradeoffs.
- Review behavior: topics raised, questions versus change requests, and revisions linked to feedback.
- Delivery context: ticket requirements, dependencies, blockers, acceptance criteria, and rework.
- Explicit rationale: the reasons recorded in discussions, design documents, and implementation plans.

Individual profiles sit within company, repository, task, and team context. Shared authorship, reviewer influence, automated formatting, and AI assistance limit attribution. Imported artifacts remain untrusted task data. Profile observations do not override current company rules.

## First pilot

Start with one approved repository, one language, and a narrow task family such as bug fixes with existing regression tests. Use task-local evidence available before each held-out historical change. Compare a generic agent and an InTap-conditioned agent using the same model and execution budget.

Agree on acceptance thresholds before running the pilot. Measure task correctness, new regression rate, reviewer minutes, revision rounds, end-to-end completion time, and model plus infrastructure cost per accepted task. Track style fit separately from correctness. Link any claimed revenue impact to a measured business outcome rather than assuming that more generated code increases revenue.

## Initial operating model

Read approved artifacts, expose profile evidence for correction, propose patches, verify them in isolation, and require review before integration. Increase autonomy only for task categories that meet the agreed evaluation criteria. No implementation in the starter framework grants production access or performs automatic merges.
