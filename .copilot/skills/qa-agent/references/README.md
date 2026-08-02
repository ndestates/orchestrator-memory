# qa-agent Specializations

The core qa-agent is general and reusable.

Project (wave) specific domain risks live in separate `*-specializations.md` files:

- `facebook-stats-specializations.md`
- `google-stats-specializations.md`
- `e-ndsign-specializations.md`
- `ndestates-io-specializations.md`
- `jerseyhouseprices-specializations.md`
- `lightstone-specializations.md`
- `mailchimp-specializations.md`

## Usage

Pass the project key when invoking:

- `/qa-agent pre-pr facebook-stats`
- `skill_args: facebook-stats` in chains
- Inside the agent: determine from scope/args and load the matching file + general checklist.

## Adding for a new wave project

1. Create `references/<slug>-specializations.md`
2. Model after an existing one (domain risks, safety, testing, process).
3. Update `qa-checklist.md` to list it.
4. Update any project-specific stack profile docs if needed.
5. Test with `/qa-agent ... <slug>` (e.g. `/qa-agent pre-pr jerseyhouseprices`)

This keeps the qa-agent portable while giving each wave project its own deep domain checks.