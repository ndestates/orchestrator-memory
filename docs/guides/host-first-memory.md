# Host-first always-on memory

[UPDATED 2026-09-17] · **3.0.0+** · **Apache-2.0 freeware**

Stable model: install the **host CLI once** with npm, use memory in **any project**, optional **VS Code / Cursor** add-in.  
You do **not** need Packagist or a paid license.

**★ End-user instructions (memory DB + vault) — please read:**  
→ **[extensions/vscode-orchestrator/INSTRUCTIONS.md](../../extensions/vscode-orchestrator/INSTRUCTIONS.md)**  
(also shipped inside the VSIX; open via **Orchestrator: Read instructions (memory + vault)**)

**Marketplace README + install channels:**  
→ **[extensions/vscode-orchestrator/README.md](../../extensions/vscode-orchestrator/README.md)**

**In-app:** Read instructions · Command Hub `Ctrl/Cmd+Shift+O` · **Memory + vault storage** · Memory Brief `Ctrl/Cmd+Shift+M` · Run /chain · skills · Setup.  
**Product straplines:** [orchestrator-memory-product.md](orchestrator-memory-product.md) · **Vault deep dive:** [knowledge-vault.md](knowledge-vault.md)

---

## Why host-first

| Old model | Host-first |
|-----------|------------|
| Copy skills into every app via `upgrade` | One `orchestrator` binary on PATH |
| Branch switches lose tools | Host package survives checkout |
| Memory only after full template deploy | `orchestrator memory …` in any folder |

Per-app `init`/`upgrade` remains optional for full skill surfaces — not required for memory.

---

## Install host CLI (users)

```bash
npm install -g @ndestates/orchestrator
orchestrator version
orchestrator memory status
```

If `python -m orchestrator_cli` is missing, install the **matching** public wheel printed by the shim (same version as npm) from [orchestrator-memory Releases](https://github.com/ndestates/orchestrator-memory/releases).

uv, pip, `install.sh`, and git clone are **maintainer** paths — see [Installation](../getting-started/installation.md#maintainer--private-factory).

Refresh later: `npm install -g @ndestates/orchestrator@latest` or `orchestrator self-upgrade --from-github --yes`.

---

## Storage (small DB + vault)

| Layer | Path | Role |
|-------|------|------|
| **SQLite** | `<project>/reports/memory/memory.db` | Runtime memory (gitignored) |
| **Global SQLite** | `~/.orchestrator/…` with `--scope global` | Cross-project optional |
| **Vault dual-write** | `reports/vault/events.jsonl` | Scrubbed durable events |
| **Inbox** | `reports/memory/inbox/` | Drop files for auto-ingest |

---

## Memory commands (CLI)

```bash
# In any project directory
orchestrator memory --help
orchestrator memory status
orchestrator memory db-path
orchestrator memory brief --seed          # session-start situation + lean brief
orchestrator memory query "what is open?"
orchestrator memory ingest --text "note" --source note
orchestrator memory ingest --file ./note.md
orchestrator memory seed                  # VERSION + git + TODO + resume
orchestrator memory list
orchestrator memory consolidate
orchestrator memory models                # full catalog (OSS + free + frontier)
orchestrator memory agents                # full agent roster
orchestrator memory watch
orchestrator memory serve --port 8888     # localhost API + inbox watch
```

### Scope

| Flag | Store location |
|------|----------------|
| `--scope project` (default) | `<cwd or --path>/reports/memory/memory.db` |
| `--scope global` | under `~/.orchestrator` (or `$ORCHESTRATOR_HOME`) |

```bash
orchestrator memory --scope global brief --seed
orchestrator memory --path /path/to/app status
```

**Never commit `memory.db`.**

---

## Session contract (agents)

1. Operator, extension, or script runs `orchestrator memory brief --seed`.  
2. Paste or attach the brief as first context for **Claude / Grok / ChatGPT / Gemini / …**.  
3. Then lean cache / TODO — memory is SSOT for “where we are” when seeded.

Chains inside a full template tree may still call `python3 scripts/session-memory-brief.py`; the **host** path is:

```bash
orchestrator memory brief --seed
```

---

## VS Code / Cursor

1. Install host CLI with npm (above).  
2. Install extension `ndestates.orchestrator-memory` (Marketplace or VSIX).  
3. Palette: **Orchestrator: Memory Brief (session start)** (and Query / Ingest / Seed / Status / Serve).  
4. Setting `orchestrator.cliPath` if the binary is not on `PATH`.

Step-by-step: [extension README](../../extensions/vscode-orchestrator/README.md).

---

## License

**Apache License 2.0** — free open source (freeware). See root `LICENSE` and `NOTICE`.

## Related

- [Always-on memory (engine)](always-on-memory.md)
- [Production ship (matching npm + wheel)](production-ship.md)
- [Installation](../getting-started/installation.md)
- [Stronger with every update](../reference/stronger-with-every-update.md)
