# Contributing

Published skills live in `skills/`. Each directory is an installable unit: its instructions, helpers, resources, and license must work together after installation in another project.

Read [AGENTS.md](AGENTS.md) before changing the repository. Use [CONTEXT.md](CONTEXT.md) for project vocabulary and [docs/adr/](docs/adr/) for durable decisions.

## Set up development

Use the Python version in [.python-version](.python-version), currently 3.14.8, to match CI. From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/check.py
```

[requirements-dev.txt](requirements-dev.txt) pins PyYAML for catalog validation. The audit helpers use Python's standard library; consumers do not need the validator's dependencies.

The default checks need curl and permission to bind a local HTTP server. Browser tests are opt-in and have [additional requirements](#run-real-browser-tests).

## Find the relevant files

| Path | Purpose |
| --- | --- |
| `skills/<name>/SKILL.md` | Agent instructions and links to bundled resources. |
| `skills/<name>/scripts/` | Executable helpers and their contract tests. |
| `skills/<name>/assets/` | Bundled assets, including pinned tool manifests. |
| `skills/<name>/agents/` | Optional agent interface metadata. |
| `scripts/check.py` | Catalog validator and Python test runner. |
| `docs/` | User guides, agent conventions, and architecture decisions. |
| `.scratch/<feature>/` | Tracked specs, tickets, and written completion evidence. |
| `.agents/skills/` | Ignored local workflow tools used to maintain this repository. |

Generated measurements, screenshots, and tool installations belong in ignored artifact directories. The [local tracker conventions](docs/agents/issue-tracker.md) define where to keep written work records.

## Check technical sources

Before relying on package, CLI, API, or configuration behavior:

1. Run `opensrc list` to inspect the available cache.
2. Resolve the relevant version from a manifest or lockfile.
3. Run `opensrc path <package>@<version>` and read the relevant source. Fetch a missing version with `opensrc fetch <package>@<version>` or its repository spec.
4. If OpenSRC cannot supply the source, state that limitation and use installed source or current official documentation. Record any uncertainty that affects the change.

For this collection, the installer examples use `skills@1.7.4`; Lighthouse is pinned in [tools-package.json](skills/lighthouse-check/assets/tools-package.json); the validation dependency is pinned in [requirements-dev.txt](requirements-dev.txt). Check the source again when changing a version or its documented behavior.

## Add or change a skill

Follow the [skill authoring guide](docs/agents/skill-authoring.md) for behavior, resource layout, and verification.

1. Work under `skills/<skill-name>/`. Set the frontmatter `name` to the directory name, using a unique lowercase name with hyphens.
2. Write a nonempty `description` of at most 1,024 characters and instructions that define the input, actions, result, and completion criteria. Names are limited to 64 characters.
3. Bundle required helpers and resources. Link them from `SKILL.md` with relative Markdown links so the validator can detect missing files. Required resources must stay inside the installed skill directory.
4. Copy the root [LICENSE](LICENSE) unchanged into the skill directory.
5. Link the skill's `SKILL.md` from the catalog in [README.md](README.md). Add or update its user guide when the public workflow changes.
6. Run the repository checks and exercise the affected workflow with realistic inputs. For packaging changes, also test installation into an unrelated project.

When moving a skill, move its complete helper and resource directories. Local workflow skills are documented in [development tooling](docs/agents/development-tooling.md); keep them outside the published catalog.

## Validate a change

Run from the repository root:

```sh
.venv/bin/python scripts/check.py
```

The command validates skill frontmatter, unique names, catalog links, bundled licenses, local resource links, optional agent metadata, and Python syntax. It then runs the repository's `test_*.py` files and those bundled under `skills/`.

HTTP contract tests use real curl requests against a local server. Audit command tests cover orchestration and report generation with controlled inputs. The browser test file is discovered too, but its tests skip unless `LIGHTHOUSE_TEST_TOOLS` is set. A passing default check therefore does not establish that Chrome or a live deployment works.

For a documentation change, verify relative links and execute the documented examples that exercise the changed instructions. For a helper or skill behavior change, keep the resulting evidence and state which scenarios remain unverified. CI runs the same validator through [validate.yml](.github/workflows/validate.yml).

## Test local installation

From an unrelated temporary project, point the installer at the absolute path to this checkout's `skills/` directory:

```sh
npx skills@1.7.4 add /absolute/path/to/skills.mflisikowski.dev/skills --list
npx skills@1.7.4 add /absolute/path/to/skills.mflisikowski.dev/skills \
  --skill lighthouse-check --agent codex
```

The list should contain the published catalog. Inspect the installed directory for the instructions, helpers, resources, and license, then run the affected workflow from the consuming project. This catches dependencies on the original checkout that catalog validation cannot detect.

Remote installation uses the revision available on GitHub. Local installation is the way to verify a change before pushing it; the repository does not require a package registry or plugin manifest.

## Run real-browser tests

Provide an installed package root containing a compatible Lighthouse, plus Node.js and Chrome/Chromium. The [tool manifest](skills/lighthouse-check/assets/tools-package.json) supplies the bundled version. Then run:

```sh
LIGHTHOUSE_TEST_TOOLS=/absolute/path/to/audit-tools \
LIGHTHOUSE_TEST_OUTPUT="$PWD/.scratch/lighthouse-check/artifacts/live-$(date +%Y%m%dT%H%M%S)" \
  .venv/bin/python skills/lighthouse-check/scripts/test_live.py
```

Choose a fresh output directory for each invocation. The tests start local HTTP fixtures and exercise compressed and uncompressed responses, mobile and desktop settings, a relocated skill directory, fragment routes, content mismatch, and a missing browser executable. `LIGHTHOUSE_TEST_OUTPUT` preserves the compression comparison artifacts; other cases use temporary directories.

Set `LIGHTHOUSE_TEST_BOOTSTRAP=1` on the same command to exercise automatic tool preparation for the uncompressed desktop case. That path additionally needs npm and network access. Browser execution and local server permissions are required in either case.

## Submit changes

Describe the resulting behavior, relevant validation, and any unverified paths. Keep specs, tickets, and written evidence in Git; leave generated audit files in ignored directories.

Write commit messages entirely in English, describing the change without coauthor or generated-by footers. For GitHub operations, use `gh` with the `mflisikowski` account.
