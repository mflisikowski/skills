# Domain context

This repository maintains reusable agent skills and distributes them from `mflisikowski/skills` on GitHub.

| Term | Meaning |
| --- | --- |
| Published skill | A self-contained directory under `skills/`, installed into another project or a user's agent environment. |
| Workflow skill | A locally installed skill under `.agents/skills/` used to develop this repository. It is excluded from the published catalog. |
| Catalog | The published skills linked in the root `README.md`. |
| Preflight | The HTTP transport checks performed by `lighthouse-check` before browser validation or Lighthouse acceptance. |

The repository uses one domain context. Record durable decisions under `docs/adr/`. Local development work lives under `.scratch/` as specified in `docs/agents/issue-tracker.md`.
