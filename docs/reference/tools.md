
# Tools

[UPDATED 2026-07-07]

To explicitly grant (or restrict) tools like bash, read_file, edit_file, etc. to a skill (or agent built from skills) in Grok Build, declare them in the allowed-tools field in the YAML frontmatter of SKILL.md.

This follows the agentskills.io spec that the skill system enforces (via validate-skill.sh and the server-side validator).

How to do it
Edit your skill’s SKILL.md like this:

---
name: my-custom-skill
description: Does X using the sandbox. Use when the user asks about ...
allowed-tools:
  - bash
  - read_file
  - edit_file
  - write_file
  - web_search
  # add only the tools this skill actually needs
---
Key points
allowed-tools is a top-level frontmatter key (alongside name, description, metadata, etc.). Any other top-level key will fail validation.
It should be a YAML list of tool names (the exact names used in function calls, e.g. bash, read_file, edit_file, write_file, web_search, browse_page, etc.).
Purpose: This is the explicit control mechanism. It lets you give a skill only the tools it needs (principle of least privilege) instead of relying on defaults.
If you omit allowed-tools, the skill currently inherits broader/default access (the system is still evolving here), but explicit declaration is the recommended and future-proof way.
After editing, run validation:
bash /root/.grok/skills/skill-creator/scripts/validate-skill.sh /home/workdir/.grok/skills/my-custom-skill

Example for vault-related skill (e.g. knowledge synthesis): declare only `read_file`, `bash` (for ledger inspection) — see guides/knowledge-vault.md and multi-AI patterns.
Where skills live
Persistent user skills: /home/workdir/.grok/skills/<skill-name>/SKILL.md (this is what you should edit/create).
Bundled skills in /root/.grok/skills/ are examples/templates — copy them into /home/workdir/.grok/skills/ if you want to customize permanently.
Example from real skills
Look at python-bug-hunter — it heavily uses bash + read_file + edit_file in its instructions, but does not yet declare allowed-tools in frontmatter (it’s an older skill). New skills should declare it explicitly.

For "agents"
If you are building higher-level agents (compositions of skills + behavior), the same pattern applies:

The agent definition (or the skill that represents the agent) declares allowed-tools.
Individual skills it calls can also declare their own (more restrictive) tool sets.
The system merges/restricts based on the active skill context.
Would you like me to show you a full minimal example skill that explicitly requests bash + file tools, or help you add allowed-tools to one of your existing skills?

## VSCode / Editor Support

A simple JSON Schema is provided at `schemas/skill.schema.json`.

It is automatically associated in this repository via `.vscode/settings.json` so that:

- `allowed-tools` (and other frontmatter fields) are no longer shown as "not supported"
- You get autocomplete for common tool names
- Basic validation of the frontmatter

The schema covers:
- `.grok/skills/**/SKILL.md`
- Synced locations (`.github/skills/`, `.claude/commands/`, `.copilot/skills/`)

If you're using VSCode on a fork, make sure the `.vscode/settings.json` and `schemas/` folder were copied (they are part of the template).

Add to chat
Explain tool validation script


Thought for 6s
validate-skill.sh is the official validation script for Grok Build skills. It enforces the agentskills.io specification so that every skill you create will pass CI and load correctly in the agent runtime.

Purpose
Single source of truth for skill quality and structure.
Mirrors the production validator (server/scripts/validate-skills.mjs) that runs on every commit.
Catches problems before you try to use the skill (wrong YAML, too much token bloat, dangerous control tokens, etc.).
Explicitly supports the new allowed-tools field you asked about in the previous question.
How to run it
bash /root/.grok/skills/skill-creator/scripts/validate-skill.sh /home/workdir/.grok/skills/my-skill-name
It takes one argument: the path to the skill directory (not the SKILL.md file itself).

If everything is good, it prints:

OK: Skill 'my-skill-name' is valid (XX lines)
If anything fails, it prints FAIL: ... and exits with code 1.

What the script actually checks
Here’s a breakdown of every rule, in the order the script enforces them:

#	Check	Why it exists	What fails it
1	SKILL.md file exists	Required by spec	Missing file
2	File starts with --- (three ASCII hyphens)	Proper YAML frontmatter	Typographic dashes (— – etc.) or no delimiter
3	Frontmatter ends with a second ---	Clean separation of metadata vs instructions	Malformed frontmatter
4	name field present + valid format	Must match directory name, kebab-case rules	Wrong name, uppercase, consecutive hyphens, too short/long
5	description field present + strict rules	This is the only thing shown before the skill loads (metadata only)	Empty, contains :  (colon-space), < or >, quoted, >1024 chars, contains "TODO"
6	compatibility (optional)	Future-proofing	Quoted or >500 chars
7	Only allowed top-level keys	Security + spec compliance	Any unknown key at the top level (e.g. version:, author:, etc.). You must put custom data under metadata:
8	allowed-tools is recognized	New field you can use to explicitly grant tools (bash, read_file, etc.)	(It is now in the allowed list)
9	Body (content after second ---) is non-empty	Skill must actually do something	Empty or only whitespace after frontmatter
10	No tokenizer control tokens (`<|...	>) anywhere in any .md` file in the skill	These are special tokens the model never sees as text — they break reasoning
11	Final line count report	Helps you stay under the ~500-line soft limit	(Just informational)
Detailed look at the most important rules
1. description is extremely strict

# These are all rejected:
description: "Use for X: foo, bar"     # contains ": "
description: Use for X <b>bold</b>     # contains < >
description: 'something'               # quoted
Reason: The description is injected into the system prompt before the skill body is even loaded. It must be a clean plain YAML scalar.

2. Allowed top-level fields (line 123 in the script)

ALLOWED_FIELDS="name description license compatibility metadata allowed-tools"
Anything else at the top level of the frontmatter will cause:

Unknown frontmatter field 'foo' — agentskills.io recognizes only: ...
This is why you put extra metadata under metadata:.

3. allowed-tools support
The script now officially recognizes allowed-tools as a valid top-level key. You can (and should) use it to explicitly declare which tools a skill is allowed to call:

allowed-tools:
  - bash
  - read_file
  - edit_file
  - write_file
4. Tokenizer control token check
This is a safety net. Tokens like <|tool_call|> or similar look like normal text to humans but get turned into special IDs by the tokenizer. Including them in skills teaches the model nothing useful and can corrupt context.

Common mistakes this script catches
Using README.md or CHANGELOG.md instead of (or in addition to) SKILL.md
Putting trigger words in the body instead of the description
Using smart quotes or em-dashes in the frontmatter
Adding custom fields directly under the --- instead of under metadata:
Forgetting that name: must exactly match the folder name
Accidentally including <|...|> tokens when copying examples
Summary
Aspect	What validate-skill.sh enforces	Benefit
Structure	Proper --- frontmatter + non-empty body	Reliable loading
Metadata quality	Strict name + description rules	Low token overhead + safe prompt injection
Tool control	Recognizes allowed-tools list	Explicit tool granting (what you asked about)
Safety	No control tokens, only allowed keys	Prevents prompt injection / model confusion
CI compatibility	Same rules as production validator	Skills that pass locally will pass in CI
Would you like me to walk through how to fix a specific validation error you’re seeing, or show you a minimal SKILL.md template that already passes this script with allowed-tools declared?
