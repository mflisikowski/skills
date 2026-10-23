# Issue tracker: local Markdown

Specs, issues, and decision maps live in tracked Markdown files under `.scratch/`. Each feature or effort has its own directory.

## File layout

| Path | Contents |
| --- | --- |
| `.scratch/<feature>/spec.md` | The agreed scope and acceptance criteria. |
| `.scratch/<feature>/issues/NN-<slug>.md` | One implementation or decision ticket, numbered from `01`. |
| `.scratch/<effort>/map.md` | A wayfinding map with Notes, Decisions-so-far, and Fog sections. |
| `.scratch/<feature>/artifacts/` | Generated files, ignored by Git. |

Keep specs, tickets, decisions, and written completion evidence in Git. Keep measurements, screenshots, and tool caches in ignored artifact directories; check [.gitignore](../../.gitignore) for the complete exclusions.

## Translate tracker operations

When a workflow says to publish to the issue tracker, create the appropriate file in the feature directory. When it says to fetch a ticket, read the referenced file. Resolve a bare ticket number within the named feature or effort; numbers are not unique across the repository.

Put `Status:`, `Blocked by:`, and, where applicable, `Type:` near the top of a ticket. Use `Blocked by: none` for an unblocked ticket or a comma-separated list of ticket numbers from the same effort. Append conversation and updates under `## Comments`.

## Implementation tickets

Use one file per ticket so it can be read and completed independently. State the required behavior and checkable acceptance criteria, and link the relevant spec or decisions. Record incoming reports with the exact [triage role strings](triage-labels.md).

Work blockers first. A ticket is unblocked when every ticket in its `Blocked by:` line is `resolved`. After its acceptance criteria pass, set `Status: resolved` and record validation under `## Completion evidence`, including any material limitations.

`resolved` is a completion state, not a triage role.

## Wayfinding tickets

The local `/wayfinder` workflow uses a map and child tickets to resolve questions before implementation. Each child records the question and a `Type:` of `research`, `prototype`, `grilling`, or `task`.

1. Scan the effort's `issues/` directory for open, unblocked, unclaimed tickets. Select the lowest number.
2. Set `Status: claimed` and save before working on it.
3. Append the answer under `## Answer`, then set `Status: resolved`.
4. Add a brief result and a relative link to the ticket in the map's Decisions-so-far section.

These tickets produce decisions. Turn the resolved map into a spec and implementation tickets when the effort is ready to build.
