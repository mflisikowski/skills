# Development tooling

Local workflow skills help maintain this repository. They live in the ignored `.agents/skills/` directory and are separate from the published catalog under `skills/`.

## Set up another checkout

The repository's validation commands work without the local workflow collection. If you want its router and engineering workflows, install the chosen tools separately. For example:

```sh
npx skills@1.7.4 add mattpocock/skills --skill ask-matt --skill setup-matt-pocock-skills --skill triage --agent codex
```

This command selects the upstream revision available at installation time. It does not reproduce the initial local snapshot. Inspect the chosen revision through OpenSRC before relying on its behavior or re-running setup.

Use `/ask-matt` to choose a workflow. The bootstrap configured a local Markdown tracker, five canonical triage roles, and one domain context. Their authoritative conventions are:

- [Issue tracker](issue-tracker.md)
- [Triage roles](triage-labels.md)
- [Domain documentation](domain.md)

Review those consumers and conventions together when updating the workflow tools. This checkout uses `CONTEXT.md`; an upstream revision may expect another filename. Keep `.agents/skills/` ignored and point catalog installation checks at this checkout's `skills/` directory.

## Provenance and licenses

The initial workflow collection was copied from the Apteo frontend checkout during bootstrap. It includes `ask-matt`, `setup-matt-pocock-skills`, `triage`, and companion skills from [mattpocock/skills](https://github.com/mattpocock/skills). Its upstream MIT notice is retained locally at `.agents/skills/LICENSE-mattpocock.txt`.

The tracked `domain.md`, `issue-tracker.md`, and `triage-labels.md` in this directory were copied or adapted from the setup skill's templates and are maintained for this repository. Their upstream notice is retained in [docs/licenses/mattpocock-skills-MIT.txt](../licenses/mattpocock-skills-MIT.txt).

See [ADR 0001](../adr/0001-separate-published-skills-from-workflow-tools.md) for the distribution boundary and [ADR 0002](../adr/0002-distribute-authored-skills-under-mit.md) for the collection's license decision. Development setup and validation are described in [Contributing](../../CONTRIBUTING.md).
