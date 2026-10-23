# Review packaging before publication

Status: resolved
Blocked by: none
Type: task

## Outcome

Review the existing bootstrap, fix concrete packaging problems, and confirm that the skill can be installed into another project with its complete resources and license.

## Findings and changes

- Reproduced a green catalog validation after deleting the complete `lighthouse-check/scripts/` directory. Converted the helper and contract-test references in `SKILL.md` into local Markdown links, which the validator checks. Added a regression test that removes the directory and requires both missing resources to be reported.
- The skills CLI copies the selected skill directory without the repository's root license. Added the selected MIT license inside the skill and made catalog validation reject missing or mismatched bundled licenses.
- The upstream license for the three copied/adapted agent-convention documents was present only inside ignored workflow tools. Retained the full notice under tracked `docs/licenses/` and documented its scope.
- Documented curl's 7.70 minimum for JSON write-out and an official-documentation fallback when OpenSRC is unavailable in a consuming project.

## Completion evidence

- `python3 scripts/check.py`: five packaging regression tests and 17 helper contract tests passed.
- Actual installation with cached `skills@1.7.4 add <checkout>/skills --skill lighthouse-check --agent codex --yes` into a temporary unrelated project found exactly one skill. All five copied files matched, and its 17 contract tests passed there.
- `preflight.py`, `test_preflight.py`, and `agents/openai.yaml` remain byte-for-byte identical to the original Apteo skill. Changes to `SKILL.md` are limited to resource/license links and the OpenSRC availability fallback.
- `gh`, using active account `mflisikowski`, confirmed that `mflisikowski/skills` is public and has no branches. Local `main` has no commits and retains the expected SSH origin. No commit or push was performed during this review.
- `.agents/skills/`, Python bytecode and generated audit evidence remain ignored. Specs and issues remain eligible for version control.

## Comments

- 2026-10-23: Review continued from the existing uncommitted bootstrap. License choice and publication rights were confirmed by the maintainer during this session.
