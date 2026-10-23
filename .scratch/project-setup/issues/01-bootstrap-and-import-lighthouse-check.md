# Bootstrap project and import lighthouse-check

Status: resolved
Blocked by: none
Type: task

## Outcome

Complete the acceptance criteria in [the setup spec](../spec.md). Preserve the original project's files and copy the first skill with all bundled scripts and UI metadata.

## Validation

Run `python3 scripts/check.py`, verify source-file hashes, and inspect Git status and ignored development tools. Record the actual result here before closing the ticket.

## Comments

- 2026-10-23: Local tracker, default triage roles, and `AGENTS.md` confirmed by the maintainer.

## Completion evidence

- 2026-10-23: `python3 scripts/check.py` passed catalog validation and all 17 helper contract tests.
- The four imported skill files were compared byte for byte with the Apteo source; all matched.
- `skills@1.7.4 add ./skills --list` discovered exactly one published skill: `lighthouse-check`.
- Negative validator fixtures rejected mismatched names, missing descriptions, and broken local resource links.
- Git ignores the 22 local development workflow skills and generated audit artifacts, while retaining specs and tickets.
- Root agent instructions, domain context, an ADR, and all three setup documents are present.
- The source Apteo working tree remained clean. All new project files await the first commit; remote publication is a separate step.
