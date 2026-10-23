# ADR 0001: Separate published skills from local workflow tools

Status: Accepted
Date: 2026-10-23

## Context

The repository needs reusable skills for consumers and engineering workflow skills for its own maintenance. The first published skill is `lighthouse-check`. Matt Pocock's existing workflow skills support local development.

## Decision

Maintain published skill sources under `skills/` and list them in the root `README.md`. Install development workflow skills under the Git-ignored `.agents/skills/` directory. Keep local specs and issues under `.scratch/` in version control; exclude generated audit artifacts.

Use one root `CONTEXT.md` and `docs/adr/`, matching the setup skill explicitly invoked during bootstrap. Use the skills CLI for initial distribution. Add plugin packaging or release automation when consumers require it.

## Consequences

The remote repository contains the authored skill catalog without redistributing the local workflow collection. Fresh checkouts must install their development workflow skills separately. Updating those tools requires checking compatibility with the repository's domain-doc convention.
