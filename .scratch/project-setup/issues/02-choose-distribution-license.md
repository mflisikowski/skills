# Choose a distribution license

Status: resolved
Blocked by: none
Type: task

## Decision

The maintainer chose MIT on 2026-10-23 and confirmed the right to publish the four imported `lighthouse-check` files under that license. Add root and bundled licenses, update distribution documentation, and verify that the license survives installation.

The upstream license for the ignored local workflow tools is retained separately. This ticket concerns this repository's authored content.

## Comments

- 2026-10-23: No license was selected during the local bootstrap.
- 2026-10-23: The maintainer selected MIT and confirmed publication rights. See [ADR 0002](../../../docs/adr/0002-distribute-authored-skills-under-mit.md).

## Completion evidence

- Root `LICENSE` and `skills/lighthouse-check/LICENSE` contain identical MIT text with `Copyright (c) 2026 Mateusz Flisikowski`.
- `README.md` documents the license scope and the requirement to retain its notice. The original Matt Pocock notice is retained in a tracked file for the three template-derived agent documents.
- `python3 scripts/check.py` passed five packaging regression tests and all 17 helper contract tests with Python 3.14.8, PyYAML 6.0.3 and curl 8.7.1.
- The official cached `skills@1.7.4` CLI installed `lighthouse-check` into an unrelated temporary project. All five installed source files matched byte for byte, including the license. All 17 contract tests also passed from that installed copy.
- Tests required execution outside the sandbox because its restrictions prevent binding the local fixture HTTP server. No remote deployment or Lighthouse audit was used for these packaging checks.
