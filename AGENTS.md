# Repository conventions

Published skills live under `skills/`. Local workflow skills in `.agents/skills/` are development tools and remain ignored by Git. Keep published skill names unique and equal to their folder names. Keep every published skill linked from the root `README.md`.

Each published skill must bundle an unchanged copy of the root `LICENSE`. Link required local resources from `SKILL.md` so catalog validation detects missing files.

When changing a helper, run `python3 scripts/check.py` with the development dependencies installed. Preserve the complete helper and resource directory when moving a skill. Validate behavior with realistic inputs; metadata validation alone does not prove a workflow works.

Before relying on software behavior, consult OpenSRC: check `opensrc list`, resolve the relevant pinned version, then inspect `opensrc path <package>@<version>`. Fetch missing sources. If unavailable, report the limitation briefly and use current authoritative documentation.

Use `gh` with the `mflisikowski` account for GitHub operations. Write all commit messages in English, describing the change without coauthor or generated-by footers.

## Agent skills

### Issue tracker

Issues and specs live as local Markdown under `.scratch/<feature-slug>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the five canonical triage roles unchanged. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `CONTEXT.md` and `docs/adr/`. See `docs/agents/domain.md`.
