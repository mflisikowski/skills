# Skills by Mateusz Flisikowski

Reusable skills for coding agents. Each skill contains instructions and the scripts or resources needed to carry out a specific task.

## Available skills

| Skill | What you get |
| --- | --- |
| [lighthouse-check](skills/lighthouse-check/SKILL.md) | A website audit with HTTP checks, browser evidence, Lighthouse measurements, and a Markdown report with recommended actions. Also supports HTTP checks alone and review of existing Lighthouse exports. |

## Install a skill

Run this in the project where you want to use the skill. The installer requires Node.js 22.20 or later and access to the GitHub repository.

```sh
npx skills@1.7.4 add mflisikowski/skills --skill lighthouse-check --agent codex
```

Add `--global` to install for your user account. Omit `--agent codex` to choose an agent interactively. Install the complete skill directory so its helpers and license travel with it.

To install an unpublished revision from a local checkout, replace `mflisikowski/skills` with the absolute path to that checkout's `skills/` directory. See [local installation](CONTRIBUTING.md#test-local-installation).

## Run your first audit

After installation, ask your agent:

```text
Use $lighthouse-check to audit https://example.com/ on mobile.
Write the report in Polish and link the resulting Markdown file.
```

The agent runs HTTP checks, confirms the page in a clean browser profile, and takes three Lighthouse measurements. It saves the report and supporting files in a unique directory under `.scratch/lighthouse-check/artifacts/` in your working directory.

An audit needs Python 3, curl 7.70 or later with compression support, Node.js 22.19 or later, and Chrome or Chromium. The agent can prepare the bundled Lighthouse tools in an isolated directory when network access and execution permissions allow it. HTTP-only checks and review of saved reports need fewer tools; see the [requirements by mode](docs/lighthouse-check.md#requirements).

## Documentation

- [Use lighthouse-check](docs/lighthouse-check.md): choose a mode, run helpers directly, read results, and resolve incomplete audits.
- [Contribute](CONTRIBUTING.md): set up development, validate changes, test installation, and add a skill.
- [Repository vocabulary](CONTEXT.md) and [architecture decisions](docs/adr/): understand the collection's structure and conventions.
- [Agent instructions](AGENTS.md): rules for agents working in this repository.

## License

The authored collection is distributed under the [MIT license](LICENSE). Each published skill includes an identical license copy for installation and redistribution.

The agent conventions adapted from Matt Pocock's templates retain their [upstream MIT notice](docs/licenses/mattpocock-skills-MIT.txt). [Development tooling](docs/agents/development-tooling.md) records their provenance.
