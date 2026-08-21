# qa-agent Specializations

The core qa-agent is general and reusable.

App-specific domain risks belong in **that app's** `references/<slug>-specializations.md`. This template does not ship other products' checklists.

## Usage

- `/qa-agent pre-pr`
- Load `references/<slug>-specializations.md` only if the app added one.

## Adding a specialization in an app

1. Create `references/<slug>-specializations.md`
2. List domain risks, safety, and testing notes
3. Keep `qa-checklist.md` general
