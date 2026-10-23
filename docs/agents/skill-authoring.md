# Skill authoring

Design for predictability: the agent should follow the intended process across runs, while adapting the output to the task.

These are authoring instructions for the agent. When available, consult the local reference `.agents/skills/writing-great-skills/SKILL.md` and its linked `GLOSSARY.md` for the underlying vocabulary. The rules below remain usable in checkouts without those ignored development files.

## Define the behavior

- Establish when the skill applies, the input it needs, the result it produces, and the boundaries of its responsibility.
- Choose ordered steps, reference material, or a combination according to the task. Give each step a checkable completion criterion; specify exhaustive coverage where omissions would matter.
- State the desired action directly. Keep prohibitions for hard boundaries and pair them with the action to take instead.
- Use established, precise concepts to anchor behavior. Define unfamiliar terms before relying on them.

## Arrange the information

- Keep instructions needed on every path in `SKILL.md`. Move material needed only on particular paths into linked resources, with an explicit condition for reading each resource.
- Keep a concept's definition, rules, and caveats together. Give each rule one authoritative home.
- Choose invocation deliberately for the target agent platform. Write descriptions around distinct triggering situations; verify platform-specific metadata against current sources.
- Split skills when they need independent invocation, or when observed rushing requires a real context boundary. Sharpen completion criteria before splitting a sequence.

## Prune and verify

- Review each sentence for a behavioral purpose. Remove duplicated meanings, stale instructions, and statements that add nothing to the agent's default behavior.
- Read readily discoverable commands and configuration from their source rather than copying them into instructions. Preserve the conventions and reasons that the environment cannot reveal.
- Exercise the skill on realistic inputs covering its intended paths and relevant failure cases. Check the agent's actions and resulting artifacts against the completion criteria.
- Revise the instruction responsible for an observed failure, then rerun the affected case. Distinguish behavioral evidence from metadata validation and report any behavior left unverified.
