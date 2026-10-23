# Development tooling

The initial `.agents/skills/` installation is a local snapshot copied from the Apteo frontend checkout used to bootstrap this project. It includes `setup-matt-pocock-skills`, `ask-matt`, `triage`, and their companion engineering skills. Its upstream is <https://github.com/mattpocock/skills>.

These files are ignored by Git and are not part of this repository's published skills. The upstream MIT license is retained with the local tools as `.agents/skills/LICENSE-mattpocock.txt`.

The tracked documents `docs/agents/domain.md`, `docs/agents/issue-tracker.md`, and `docs/agents/triage-labels.md` were copied or adapted from the setup skill's templates. Their original copyright and MIT permission notice are retained in [docs/licenses/mattpocock-skills-MIT.txt](../licenses/mattpocock-skills-MIT.txt), which is published with this repository.

The invoked setup and the imported skills use root `CONTEXT.md`. Newer upstream revisions use `GLOSSARY.md`. Review the domain-doc convention when updating the workflow tools; update the consumers and `docs/agents/domain.md` together.

On another checkout, install your chosen workflow skills locally with the skills CLI, for example:

```sh
npx skills@1.7.4 add mattpocock/skills --skill ask-matt --skill setup-matt-pocock-skills --skill triage --agent codex
```

That installs the upstream revision available at installation time, rather than reproducing this initial local snapshot. Review its conventions before re-running setup. Keep `.agents/skills/` ignored; validate this repository's catalog by pointing the installer at `./skills`.
