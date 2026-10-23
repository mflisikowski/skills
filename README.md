# Skills by Mateusz Flisikowski

Reusable agent skills built from practical engineering workflows.

## Available skills

| Skill | Use it for |
| --- | --- |
| [lighthouse-check](skills/lighthouse-check/SKILL.md) | Ask the agent to run HTTP preflight and Lighthouse, then save a Markdown report with evidence and recommendations. Also supports preflight-only checks and existing reports. |

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

After installation, ask the agent, for example: “Use `$lighthouse-check` to audit https://example.com/ and save a report in Polish.” The agent runs the tools and delivers a linked Markdown file. You can also request only the HTTP checks or analysis of existing Lighthouse JSON/HTML reports.

`lighthouse-check` uses Python 3 and curl 7.70 or later with compression support. Full measurement also needs Node.js compatible with the selected Lighthouse version and Chrome/Chromium. The agent discovers project tools or prepares the bundled Lighthouse version in an isolated audit directory; it leaves application dependencies untouched. The bundled version requires Node.js 22.19 or later. Missing prerequisites or access produce an incomplete report with the reason. Preparation requires network access and the environment's execution permissions.

Full audits default to three sequential mobile runs with fresh browser profiles. Results include a Markdown report, HTTP evidence, a browser screenshot, each Lighthouse JSON report, settings, versions, medians and ranges. Output goes under a unique `.scratch/lighthouse-check/artifacts/` directory. The first supported live scenario is public anonymous navigation; authenticated workflows need explicit scenario handling by the agent. HTTP findings remain visible even when a diagnostic Lighthouse measurement can proceed.

## Develop

Python 3.14.8 is the development and CI baseline. Create an isolated environment and run the checks:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/check.py
```

The check validates the published catalog, bundled licenses and resource links, then runs validator and bundled Python helper tests. Helper tests use a local HTTP server and actual curl requests; no deployed website is needed.

The real-browser contract test is opt-in. Set `LIGHTHOUSE_TEST_TOOLS` to the absolute package root containing an installed Lighthouse and run `python3 skills/lighthouse-check/scripts/test_live.py`. It measures compressed and uncompressed fixtures with real Chrome after relocating the skill, checks mobile and desktop profiles, and preserves all attempts when `LIGHTHOUSE_TEST_OUTPUT` points to a fresh artifact directory. This test requires browser execution permissions; it is separate from the default checks.

Set `LIGHTHOUSE_TEST_BOOTSTRAP=1` as well to verify automatic preparation in a fresh isolated directory for the desktop case. This additional path downloads tools and requires network access.

Add your reusable skills under `skills/<skill-name>/`. Keep instructions in `SKILL.md`; include scripts, references, or assets when the workflow needs them, and link required local resources so validation detects missing files. Include an unchanged copy of the root `LICENSE` in each skill directory. Update the table above whenever the published catalog changes.

Local Matt Pocock workflow skills live in the ignored `.agents/skills/` directory. They help maintain this project and are excluded from the published catalog. See [development tooling](docs/agents/development-tooling.md).

Work is tracked in local Markdown under `.scratch/`. Start with [the project setup spec](.scratch/project-setup/spec.md). Agent conventions are in [AGENTS.md](AGENTS.md).

## Distribution

GitHub is the distribution source. The first publication is still pending. No package registry or plugin manifest is required for installation through the skills CLI.

The collection is available under the [MIT license](LICENSE), including its instructions, scripts and documentation. You may use, modify and redistribute it commercially while retaining the copyright and license notice. Each skill bundles its own copy of the license so it remains available after installation.

Development documentation adapted from Matt Pocock's templates retains its [upstream MIT notice](docs/licenses/mattpocock-skills-MIT.txt); see [development tooling](docs/agents/development-tooling.md) for the affected files.
