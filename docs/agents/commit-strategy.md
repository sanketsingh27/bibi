# Commit Strategy

## Branches and integration

- `dev` is the integration branch. Create feature branches from the latest
  developer-synchronized `dev` and target feature PRs at `dev`. Fetch `origin`
  when available and incorporate `origin/dev` before branching if it exists;
  until `dev` is published, use local `dev`.
- Use the ticket number alone as the feature branch name, such as `42`, without
  a prefix or description. Related sequential tickets share the first ticket's
  numbered branch and record that assignment in every affected ticket.
- Related tickets may run sequentially on one feature branch. Record the exact
  branch, base `dev`, shared tickets, execution order, and assigned worktree in
  their ticket contracts. Parallel features use distinct branches.
- Keep commits scoped to one ticket; include its implementation, tests,
  migrations, and required documentation. Identify the ticket in each commit.
- Before committing, inspect the staged changes and exclude unrelated work.
  Commit only when the user authorizes it; report actual verification results.
- A related dependent ticket may start in a fresh authorized session after its
  prerequisite is verified and committed on the shared branch. Record the
  required test/runtime results and commit in the handoff. Dependencies from
  other feature branches must be accepted, merged into `dev`, and available in
  the implementing worktree before dependent implementation starts.
- Merge feature PRs into `dev` only after all included tickets are accepted and
  the user authorizes merging. Close tickets only with user authorization.
- Review the combined changes on `dev` before promoting them to `main` with
  separate user authorization. The developer maintains synchronization from
  `main` into `dev`, including fixes made directly to `main`.

## Two reusable implementation worktrees

1. Maintain two reusable implementation worktrees, `../feature-one` and
   `../feature-two`, alongside the primary checkout. Each has one active feature
   branch and one active implementation session. Record its path and owner in
   the ticket/handoff before work starts.
2. Use an available worktree for a new feature. Synchronize `dev` as described
   above and create the assigned numbered branch from it. If `dev` does not yet
   exist, report that setup prerequisite before implementation.
3. Related tickets retain their feature branch and worktree across fresh
   sessions. Release the previous session's ownership before the next starts.
   Keep a worktree reserved while its feature PR awaits acceptance or merging.
4. After the feature PR is merged into `dev`, release the session and confirm
   there are no uncommitted changes or unresolved Git operations. Fetch `origin`,
   synchronize `dev`, then park the worktree detached at `dev` or create the next
   assigned numbered branch from it. Detached HEAD is an idle state only;
   implementation requires the ticket's exact assigned branch.
5. Delete the old local feature branch only after verifying its PR was merged
   and switching the worktree away from it. Branch cleanup requires user
   authorization; preserve uncommitted work and use authorized cleanup if a
   squash merge prevents normal branch deletion.
6. When both worktrees are occupied, queue new features. Create an additional
   worktree only when the user explicitly authorizes more parallel work.
