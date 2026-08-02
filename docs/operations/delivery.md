# Delivery

[UPDATED 2026-07-07] — refreshed; vault graph ledger supports audit in delivery/compound (secure events).

## Overview

Work flows from feature branches through `develop` to `master` using pull requests. Automated draft PRs assist promotion.

## Before you begin

- On a `feature/*` branch with clean scope vs TODO
- Audit gates pass (see [Testing](testing.md))

## Steps

1. **Align branch context** (optional):

   ```text
   /chain delivery
   ```

   Or `/branch-context-agent` alone with `no chain`.

2. **Stage and commit** with a clear message. Use conventional prefixes: `feat`, `fix`, `docs`, `chore`.

3. **Set upstream** on first push:

   ```bash
   git push -u origin feature/your-branch
   ```

4. **Promotion PRs** — pushing `feature/**` opens a draft PR to `develop`; pushing `develop` opens a draft PR to `master` (`branch-promotion-prs.yml`).

5. **Review** draft PRs in GitHub before marking ready.

## Branch rules

| Branch | Rule |
|--------|------|
| `feature/*` | Day-to-day work |
| `develop` | Integration; PR required |
| `master` | Production; PR required |

Do not force-push protected branches.

## Verify

- `git status` clean after commit
- `bash scripts/chain-audit.sh` still 100/100 if chains/registry changed
- Draft PR visible on GitHub when applicable

## Next steps

- [Daily workflow](../guides/daily-workflow.md)
- [Testing](testing.md)
- [Conventions cache](../codebase/CONVENTIONS.md)

## Related

- [Operations index](index.md)