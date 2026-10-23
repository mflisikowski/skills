# Repository vocabulary

This repository maintains reusable agent skills for installation in other projects. Its GitHub distribution source is `mflisikowski/skills`.

| Term | Meaning |
| --- | --- |
| Published skill | A self-contained directory under `skills/` intended for distribution, including `SKILL.md`, required resources, and a copy of the root license. |
| Workflow skill | A locally installed skill under the ignored `.agents/skills/` directory, used to maintain this repository. |
| Catalog | The published skills linked in the root `README.md`. |
| Preflight | The bounded HTTP transport checks performed by `lighthouse-check`, covering the document and selected resources. Its verdict is separate from audit execution status. |
| Audit | The evidence-collection workflow and resulting report. A full audit combines preflight, browser scenario validation, and Lighthouse measurements. |
| Report review | Offline analysis of saved Lighthouse exports. It makes no observation about the current deployment. |
| Deployment acceptance | An assessment that the intended deployment meets the requested criteria. Completing an audit alone does not establish acceptance. |
| Artifact | A generated measurement, screenshot, log, or report kept under an ignored artifact directory. Written ticket completion evidence can reference artifacts while remaining tracked. |

The repository has one domain context. Use these terms in code, issues, and documentation. Record durable decisions under [docs/adr/](docs/adr/) and development work under [.scratch/](.scratch/README.md), following the [tracker conventions](docs/agents/issue-tracker.md).
