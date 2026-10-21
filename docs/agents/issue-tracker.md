# Issue tracker: GitHub

Issues and specs live in GitHub Issues for `sanketsingh27/bibi`.
Use the `gh` CLI. Inside this clone, `gh` resolves the repository from
`origin`; outside it, pass `--repo sanketsingh27/bibi` to issue and PR commands.

## Conventions

- Create: `gh issue create --title "..." --body "..."`. Use a heredoc for multiline bodies.
- Read: `gh issue view <number> --comments`; fetch labels with `gh issue view <number> --json labels`.
- List: `gh issue list --state open --json number,title,body,labels,comments`, with appropriate label and state filters.
- Comment: `gh issue comment <number> --body "..."`
- Apply or remove labels: `gh issue edit <number> --add-label "..."` or `--remove-label "..."`
- Close: `gh issue close <number> --comment "..."`

Use the role mapping in `triage-labels.md` when applying triage labels.

## Pull requests as a triage surface

**PRs as a request surface: no.**

If changed to `yes`, triage external PRs using the same labels and states:
- Read: `gh pr view <number> --comments` and `gh pr diff <number>`.
- List: `gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments`.
  Keep author associations `CONTRIBUTOR`, `FIRST_TIME_CONTRIBUTOR`, or `NONE`.
- Comment, label, or close with `gh pr comment`, `gh pr edit`, or `gh pr close`.

GitHub shares issue and PR numbers. When the surface is unknown,
try `gh pr view <number>` and fall back to `gh issue view <number>`.

## Publishing and fetching

When a skill says "publish to the issue tracker", create a GitHub issue.
When it says "fetch the relevant ticket", run `gh issue view <number> --comments`.

## Wayfinding operations

Used by `/wayfinder`.

- Map: an issue labelled `wayfinder:map` containing Notes, Decisions-so-far, and Fog.
- Child ticket: link an issue to the map using GitHub sub-issues. If unavailable,
  use a task list in the map and `Part of #<map>` in each child.
  Label children `wayfinder:<type>`: `research`, `prototype`, `grilling`, or `task`.
- Blocking: use native issue dependencies:
  `gh api --method POST repos/sanketsingh27/bibi/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`.
  Get the database ID with
  `gh api repos/sanketsingh27/bibi/issues/<blocker-number> --jq .id`.
  If dependencies are unavailable, use `Blocked by: #<n>, #<n>` in the child body.
  A child is unblocked when all blockers are closed.
- Frontier: inspect the map's open children; exclude assigned tickets and those
  with open blockers. Native `issue_dependencies_summary.blocked_by > 0`
  indicates open blockers. Otherwise inspect the `Blocked by` line.
  Choose the first eligible ticket in map order.
- Claim: `gh issue edit <number> --add-assignee @me` before starting work.
- Resolve: comment with the answer, close the child, then append a gist and link
  to the map's Decisions-so-far.
