# agent.md

Project-wide behavioral guidelines and feature development workflow. Read this file before planning features, preparing tickets, implementing tickets, or verifying their completion.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For feature planning and ticket implementation, follow the gated workflow in section 6.

For multi-step tasks, state a brief plan:

```text
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Codebase Exploration and Search

**Use the graph to navigate. Verify against the source.**

- Use the `graphify` skill when exploring the codebase, architecture, file relationships, or data flow.
- If `graphify-out/graph.json` exists, query the existing graph first rather than rebuilding it: `graphify query "<question>"`.
- Use `graphify path "<source>" "<target>"` to trace relationships and `graphify explain "<symbol>"` to explore a node.
- Read the relevant source files before editing; distinguish extracted relationships from inferred or ambiguous ones.
- Follow the skill's build or update workflow when the graph is missing or stale.
- For shell-based text searches, use `rg` instead of `grep`.

## 6. Feature Development Workflow

**Plan in one session. Implement approved tickets in fresh sessions on their assigned branches.**

These gates apply across the project, including parallel worktrees. Follow the named skills in order; this workflow adds approval, session, and branch requirements to their processes. Planning produces documentation and issues, not feature implementation.

**Enter at the applicable phase.** Start at the earliest phase whose prerequisites are not satisfied. Creating tickets from an existing approved spec starts at Phase 4; publishing already approved ticket drafts resumes Phase 4 at publication. Verify existing approvals against the current scope, but do not repeat completed phases merely because this file was reread or a new session started. Missing approval or a material scope change still requires the relevant approval gate.

### Phase 1: Report the planning model (non-blocking)

1. When starting a new feature's planning, report the active model and thinking/reasoning level once from session metadata or a read-only status command. If either is not exposed, say it is unverified; do not guess.
2. Continue with the current settings without asking for model confirmation. Unavailable model metadata does not block planning or ticket creation. Re-reading this workflow does not restart this reporting step.
3. If the feature's complexity or risk warrants a different model or reasoning level, explain the recommendation as advisory, not an approval gate.
4. Model and thinking-level changes remain manual: the user changes them through their client. Never change model settings, thinking level, or defaults automatically. After a user-requested change, recheck exposed settings if available; otherwise report them as unverified and continue.

### Phase 2: Grill and document

1. Use `/grill-with-docs`, which combines `grilling` and `domain-modeling`, to resolve requirements, assumptions, scope, tradeoffs, and open decisions.
2. Find codebase facts using section 5; ask the user only about decisions or information unavailable from the repository and tools.
3. Record settled domain terminology in the root `CONTEXT.md` and architecture decisions in `docs/adr/`, following `docs/agents/domain.md`.
4. Proceed only when the user confirms shared understanding and no unresolved decision blocks specification.

### Phase 3: Create the spec

1. Use `/to-spec` to synthesize the agreed design into a spec. Follow its testing-seam confirmation step; use existing behavioral test seams where possible.
2. Publish the spec as a GitHub issue in `sanketsingh27/bibi`, following `docs/agents/issue-tracker.md`. This is the parent specification, not an implementation ticket.
3. Include scope, non-goals, user-visible behavior, implementation decisions, and testing decisions. Surface unresolved blockers rather than inventing answers.
4. Ask the user to verify the published spec before converting it into tickets. A skill-applied `ready-for-agent` label does not authorize implementation of the parent spec.

### Phase 4: Draft, verify, and publish tickets

1. Use `/to-tickets` on the approved spec to produce small, independently verifiable vertical slices with explicit blocking edges.
2. Include the ticket contract below in every draft. Present the breakdown, tests, success criteria, dependencies, and proposed branches; ask the user to verify and approve the tickets before publishing.
3. Publish approved tickets as GitHub issues in dependency order. Reference the parent spec and use native blocking relationships where available, following `docs/agents/issue-tracker.md`.
4. Once issue numbers exist, replace proposed branch placeholders with exact issue-scoped branch names, such as `feature/42-save-filter`. Follow `docs/agents/commit-strategy.md`; each ticket owns one unique branch.
5. Verify every published ticket has the full contract and an exact branch before marking it `ready-for-agent`. Return the issue links, ticket-to-branch mapping, blockers, and currently unblocked tickets.

#### Required ticket contract

Each ticket body must contain:

- **Parent spec:** its GitHub issue link, with the relevant user stories or decisions.
- **What to build and out of scope:** one complete user-visible slice and its boundaries.
- **Branch:** the exact assigned branch; **base branch:** the repository's actual integration branch. Record the worktree path when assigned.
- **Blocked by:** specific issue links, or `None`; include unresolved decisions, missing credentials, and other prerequisites separately.
- **Acceptance criteria:** checkable conditions describing successful behavior, including relevant boundaries and error cases.
- **Tests:** behavioral scenarios, the test seam, relevant existing tests to run or extend, exact runnable commands and working directories, and expected results. New regression tests must catch plausible consumer-visible failures; do not add tests just to satisfy a count.
- **Runtime verification:** a runnable smoke command or manual scenario with the expected observable outcome. Tests alone do not replace exercising the changed path.
- **Approval and completion evidence:** the user's ticket approval and implementation authorization, followed by actual verification results and final user acceptance when available. Do not invent approvals or passing results.

No ticket is ready with missing tests, vague success criteria, an unresolved branch placeholder, or an unrecorded blocker. For behavior requiring manual verification, specify the exact steps and expected outcome.

### Phase 5: Authorize and hand off

1. After ticket verification and publication, ask the user which unblocked tickets to implement. Ticket approval, publication, labels, or silence are not implementation authorization.
2. An unresolved blocker prevents implementation of that ticket; independent approved tickets may proceed. A dependency is satisfied only when its accepted changes are integrated into the ticket's base and available in its worktree, not merely because its issue is closed.
3. Once authorized, provide a fresh-session handoff containing the ticket and spec links, exact branch, base, worktree path if assigned, dependency state, authorization, and verification commands.
4. All ticket implementation starts in a new session using the client's configured default model, not an inherited planning-session override. Do not hard-code a model name. Verify this from exposed session settings or ask the user to confirm if not observable; any correction remains manual.
5. End the planning session at the handoff. Do not implement there or simulate a fresh session by clearing context. If the client cannot launch a new session, provide the handoff for the user to open one manually.

### Phase 6: Enforce worktree ownership and implement

1. In the fresh session, read this workflow and the assigned ticket, spec, and comments. Confirm explicit authorization and satisfied blockers before implementation.
2. Verify the working directory with `git rev-parse --show-toplevel`, the active branch with `git branch --show-current`, and worktree registration with `git worktree list --porcelain`. Compare the active branch exactly with the ticket's recorded branch.
3. A missing assignment, detached HEAD, mismatched branch, or conflicting worktree owner is a hard stop before editing. Report the expected branch and observed state; do not silently switch branches, rewrite the ticket's assignment, or implement another branch's ticket.
4. Use one ticket branch per worktree and one active implementation session per ticket/worktree. Multiple worktrees may implement independent, authorized tickets on distinct branches; they must not edit each other's worktrees. Prepare a dedicated worktree on the assigned branch before launching its implementation session.
5. Implement only the assigned ticket using the relevant skills and existing patterns. Keep implementation, tests, migrations, and required documentation on its branch. Follow the commit strategy; do not start another ticket in the same session.

### Phase 7: Prove completion and request acceptance

1. Run the ticket's specified behavioral tests and exercise its runtime verification scenario. Check every acceptance criterion against observed evidence.
2. Report commands, working directories, results, and remaining blockers on the ticket. An unrun or failed required check means the ticket is not complete.
3. Ask the user to verify the result and accept the ticket. Until acceptance, keep it open and do not merge it; address requested corrections within the same ticket's scope and branch.
4. After acceptance, close or merge only when the user authorizes those actions. Hand off subsequent tickets to their own fresh default-model sessions and assigned worktrees.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## Agent skills

### Issue tracker

Issues and specs live in GitHub Issues for `sanketsingh27/bibi`. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the five default triage labels. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `CONTEXT.md` and `docs/adr/`. See `docs/agents/domain.md`.
