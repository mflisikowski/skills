# Domain documentation

This repository has one domain context. Its vocabulary lives in root [CONTEXT.md](../../CONTEXT.md), and durable decisions live in [docs/adr/](../adr/).

## Before exploring

Read `CONTEXT.md` and the ADRs relevant to the work. Use their terms and decisions when writing code, tests, issues, and proposals.

If a needed concept is absent, resolve its meaning before adding a glossary entry. The local `/domain-modeling` workflow can help settle fuzzy or overloaded terms. Add documentation when a term or decision is resolved; missing files alone are not a reason to create placeholders.

## Record changes

- Keep definitions in `CONTEXT.md`, with one meaning per term.
- Record a durable decision as a numbered Markdown file under `docs/adr/`, following the existing records' context, decision, and consequences structure.
- When a proposal conflicts with an accepted ADR, identify the record and explain why it should be reconsidered before changing the convention.

The local workflow tools were configured to consume `CONTEXT.md`. If an upstream update expects another filename, review the consumers and this convention together. See [development tooling](development-tooling.md).
