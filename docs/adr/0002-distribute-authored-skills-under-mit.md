# ADR 0002: Distribute authored skills under MIT

Status: Accepted
Date: 2026-10-23

## Context

The collection is intended for installation and reuse in other projects. Skills include both instructions and executable helpers. The skills CLI copies an individual skill directory, so a license located only at the repository root would be absent from that installation.

## Decision

Distribute the authored collection under the MIT license, with copyright attributed to Mateusz Flisikowski. Keep the canonical text in root `LICENSE` and an identical copy in every published skill directory. Catalog validation checks that each copy is present and matches.

The maintainer chose MIT and confirmed the right to publish the four imported `lighthouse-check` files under that license on 2026-10-23. The ignored Matt Pocock workflow tools retain their separate upstream license. The three tracked agent-convention documents derived from those tools retain the upstream notice in `docs/licenses/mattpocock-skills-MIT.txt`.

## Consequences

Consumers may use, modify and redistribute the skills, including commercially, subject to retaining the copyright and permission notice. The same license covers the authored instructions, scripts and documentation. License changes must update the root file and all bundled copies together.

## Sources

- [MIT license text](https://opensource.org/license/mit)
- [GitHub repository licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
- `skills@1.7.4`, `src/installer.ts`: `copyDirectory` copies the selected skill directory and does not add files from the repository root; verified through OpenSRC.
