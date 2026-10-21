# Domain Docs

This repository uses a single-context layout.

## Before exploring

- Read `CONTEXT.md` at the repository root.
- Read relevant architecture decision records under root `docs/adr/`.

If these files do not exist, proceed silently. Do not flag their absence or
suggest creating them upfront. Domain-modeling workflows create them lazily
when terminology or architectural decisions are resolved.

## Layout

- `CONTEXT.md`: domain glossary and context.
- `docs/adr/`: architecture decision records.

## Use the glossary's vocabulary

Use terms defined in `CONTEXT.md` when naming domain concepts in issues,
proposals, hypotheses, and tests. Follow any explicitly avoided synonyms.

If a needed concept is absent, check whether it reflects existing project
language. Note genuine glossary gaps for `/domain-modeling`.

## Flag ADR conflicts

If a proposal contradicts an existing ADR, identify that ADR and explain
why the decision should be reopened rather than silently overriding it.
