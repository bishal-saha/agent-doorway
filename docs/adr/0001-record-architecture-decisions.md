# ADR 0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-11-23

## Context

Agent Doorway is a reference implementation: readers should be able to see not only *what* was
built but *why*. Design choices made in a chat, a commit message or someone's head get lost, and
later contributors repeat old debates.

## Decision

Every significant architecture decision is written down as a short Architecture Decision Record in
`docs/adr/NNNN-title.md`, numbered in order, using this format: Status, Date, Context, Decision,
Consequences. An ADR is never edited after it is accepted, except to mark it *Superseded by ADR
NNNN*; a changed decision gets a new ADR.

"Significant" means: hard to reverse, affects more than one module, or a reader would ask "why
not X?".

## Consequences

- Reviewers can follow the reasoning behind the structure without asking.
- Each ADR costs a few minutes to write; that is cheaper than re-arguing a decision.
- The ADR list doubles as a changelog of the architecture.
