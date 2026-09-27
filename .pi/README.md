# Papersmith AI — Pi harness directory

This directory looks almost empty in a fresh clone, and that is correct: the
only thing Pi needs here is `skills`, and `skills` is **generated**, not
versioned.

```
npm run setup:harnesses
```

That command links `.pi/skills -> ../skills`, the one canonical tree every
harness reads. The link is a relative symlink rebuilt on demand rather than a
fourth copy of the skills, because four copies of one tree are four things that
can drift from each other while all four look equally authoritative.

This file exists so the directory itself travels with the repository. Without
it a collaborator cloning the repo sees `.claude/`, `.opencode/` and
`.antigravity/` and no `.pi/` at all, and reasonably concludes Pi is not a
supported harness — or opens Pi, which creates its own empty directory pointing
nowhere. Pi is supported; `PI.md` at the repository root is its entrypoint.

Pi receives no generated slash commands. Only `claude` and `opencode` produce
command files; Antigravity and Pi invoke a capability by name and the agent
reads `skills/<name>/SKILL.md` before the work starts.
