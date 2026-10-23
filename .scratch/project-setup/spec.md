# Bootstrap the skills repository

## Goal

Create a local working repository at `~/mfd-projects/skills.mflisikowski.dev`, connected to `mflisikowski/skills`, with the first reusable skill and a consistent engineering workflow.

## Scope

- Configure local Markdown tracking, canonical triage roles, and single-context domain docs through `setup-matt-pocock-skills`.
- Install the current project's Matt Pocock workflow skills as local development tools.
- Import the full `lighthouse-check` directory without changing its behavior.
- Document installation, development, and catalog conventions.
- Add metadata/resource validation and run the existing helper contract tests.

## Acceptance

- The repository has the expected GitHub remote and root `AGENTS.md`.
- `docs/agents/` describes the tracker, triage vocabulary, and domain-doc consumption.
- `skills/lighthouse-check/` matches the source skill's four files byte for byte.
- Published skill validation and bundled helper tests pass locally.
- Only the authored skill is present in the tracked published catalog.

GitHub publication, a license decision, plugin packaging, and automated releases are outside the initial local setup.

## Tickets

- [01: Bootstrap project and import lighthouse-check](issues/01-bootstrap-and-import-lighthouse-check.md)
- [02: Choose a distribution license](issues/02-choose-distribution-license.md)
- [03: Review packaging before publication](issues/03-review-packaging-before-publication.md)

## Follow-up review

The byte-for-byte import requirement above describes the initial bootstrap. Subsequent review may improve the published instructions and packaging; retain the original helper behavior and record those changes in the follow-up ticket. The license decision is recorded in ADR 0002. Publication remains a separate step.
