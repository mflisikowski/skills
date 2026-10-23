# Skills by Mateusz Flisikowski

Reusable agent skills built from practical engineering workflows.

## Available skills

| Skill | Use it for |
| --- | --- |
| [lighthouse-check](skills/lighthouse-check/SKILL.md) | Verify deployed HTTP compression and browser readiness before Lighthouse, or review reports against their test conditions. |

## Install

After the first commit is pushed to GitHub, run this from the project where you want to use the skill:

```sh
npx skills@1.7.4 add mflisikowski/skills --skill lighthouse-check --agent codex
```

Omit `--agent codex` to choose an agent interactively. Add `--global` for a user-wide installation.
The installer requires Node.js 22.20 or later. Install the complete skill directory, including its scripts.

To test this checkout locally before publishing:

```sh
npx skills@1.7.4 add /absolute/path/to/skills.mflisikowski.dev/skills --list
```

`lighthouse-check` needs Python 3 and curl 7.70 or later with compression support for its transport helper. Actual browser checks and Lighthouse measurement also need the appropriate browser and audit tooling. The skill does not install those tools.

## Develop

Python 3.14.8 is the development and CI baseline. Create an isolated environment and run the checks:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/check.py
```

The check validates the published catalog, bundled licenses and resource links, then runs validator and bundled Python helper tests. Helper tests use a local HTTP server and actual curl requests; no deployed website is needed.

Add your reusable skills under `skills/<skill-name>/`. Keep instructions in `SKILL.md`; include scripts, references, or assets when the workflow needs them, and link required local resources so validation detects missing files. Include an unchanged copy of the root `LICENSE` in each skill directory. Update the table above whenever the published catalog changes.

Local Matt Pocock workflow skills live in the ignored `.agents/skills/` directory. They help maintain this project and are excluded from the published catalog. See [development tooling](docs/agents/development-tooling.md).

Work is tracked in local Markdown under `.scratch/`. Start with [the project setup spec](.scratch/project-setup/spec.md). Agent conventions are in [AGENTS.md](AGENTS.md).

## Distribution

GitHub is the distribution source. The first publication is still pending. No package registry or plugin manifest is required for installation through the skills CLI.

The collection is available under the [MIT license](LICENSE), including its instructions, scripts and documentation. You may use, modify and redistribute it commercially while retaining the copyright and license notice. Each skill bundles its own copy of the license so it remains available after installation.

Development documentation adapted from Matt Pocock's templates retains its [upstream MIT notice](docs/licenses/mattpocock-skills-MIT.txt); see [development tooling](docs/agents/development-tooling.md) for the affected files.
