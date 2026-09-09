## Core engineering standards

### 1. Think Before Coding

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

- No features beyond what was asked. No abstractions for single-use code.
- No configurability that wasn't requested. No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
- The test: would a senior engineer say this is overcomplicated?

### 3. Surgical Changes

- Don't 'improve' adjacent code, comments, or formatting. Match existing style even if you'd do it differently.
- Remove imports and variables that YOUR change orphaned. Leave pre-existing dead code alone — mention it instead.
- The test: every changed line must trace directly to the request.

### 4. Goal-Driven Execution

- Turn the task into a verifiable goal before starting. 'Fix the bug' becomes 'write a test that reproduces it, then make it pass'.
- For multi-step work, state the plan as `step -> verify:` pairs.
- Weak criteria ('make it work') force constant clarification. Strong criteria let you loop unattended.

### 5. Execute Before You Claim

- Never assume code works until it has been executed. Passing tests are not proof it works — a server that won't boot passes every unit test.
- Always give yourself a validation mechanism: a dev server, a fixture file, a known-good output to diff against.
- Red before green. Confirm the new test FAILS before implementing, or you may be testing nothing.
- A bug found by hand gets fixed via red/green TDD, so it becomes a permanent regression test.

### 6. Don't Inflict Unreviewed Code

- Never open a PR containing code you have not read yourself. The first review pass is your job, not the reviewer's.
- Several small PRs beat one big one. Splitting commits is cheap when an agent does the git work.
- Review the PR description too — agents write convincing ones that are wrong.
- Include evidence: how you tested it, why you chose this implementation, screenshots if it's visual.

### 7. Hoard What You Know How To Do

- A trick only has to be worked out once. Save the working example to `references/` and point future agents at it.
- Prefer 'build X by combining these two working examples' over describing the mechanics from scratch.
- 'Similar to how `<existing thing>` works' replaces a spec. Clone a reference repo to a temp dir rather than paraphrasing it.
- End a task with the compound step: fold what you learned back into this YAML or a skill. Small improvements compound.

### 8. Work With The Grain Of The Harness

- Fetch raw source with `curl`, not a summarising fetch tool, when you need the actual bytes.
- Scratch work goes in a temp directory so it can never be committed by accident.
- Never retype code into a document — emit it by running `cat`/`sed`/`grep` so it cannot be hallucinated.
- A subagent must justify itself on token economics, not role-play. Fan out only over genuinely independent work.

## Definition of done

A change is not finished until:

- It works, and you have *seen* it work.
- It solves the right problem — the one that was actually asked.
- Failure paths are handled, and errors say enough to debug them.
- It is the minimum code that does the job.
- Tests cover it, and they failed before the implementation existed.
- Docs that the change invalidated have been updated.
- It doesn't make the next change harder than it needs to be.
