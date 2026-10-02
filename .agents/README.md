# Papersmith AI — `.agents` directory (Google Antigravity)

This directory looks almost empty in a fresh clone, and that is correct: the
only thing Antigravity needs here is `skills`, and `skills` is **generated**,
not versioned.

```
npm run setup:harnesses
```

That command links `.agents/skills -> ../skills`, the one canonical tree every
harness reads. Antigravity invokes each skill as `/name`. The link is a relative
symlink rebuilt on demand rather than another copy of the skills.

`.antigravity/skills` is a second link to the same tree, kept for now for
workspaces that already reference it. `.antigravity/rules.md` is the generated
Antigravity entrypoint.

This file exists so the directory itself travels with the repository.
