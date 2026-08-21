// Orchestrator Memory — AI token cache
// Slash commands in Command Palette (/session-start) + Chat (@orchestrator /session-start)
// Same / text works in Claude, Grok, Cursor, Copilot, Gemini.
// Apache-2.0 · host CLI: uv / pip / npm install orchestrator
"use strict";

const vscode = require("vscode");
const { spawn, spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

/** Last GitHub Release that always has a wheel (override via settings). */
const DEFAULT_PUBLISHED_CLI = "2.2.0";

/** Built-in chains always available (even without chains/registry.yaml). */
const BUILTIN_CHAINS = [
  { id: "session-start", name: "Session start", description: "New day / after eod — vault + lean cache" },
  { id: "session-resume", name: "Session resume", description: "Same-day return after mid-day session-end" },
  { id: "session-end", name: "Session end", description: "Mid-day pause (resume via session-resume)" },
  { id: "eod-shutdown", name: "End of day", description: "EOD vault + resume card" },
  { id: "always-on-memory", name: "Always-on memory", description: "Ingest / consolidate / brief" },
  { id: "delivery", name: "Delivery", description: "Ship-ready path" },
  { id: "code-review", name: "Code review", description: "Diff-scoped review" },
  { id: "daily-standup", name: "Daily standup", description: "Standup + cache" },
  { id: "cache-rebuild", name: "Cache rebuild", description: "Refresh docs/codebase cache" },
];

/** Slash catalog — IDE helpers. Models/Grok/Claude use /chain <id> natively. */
const SLASH_CATALOG = [
  {
    slash: "/chain session-start",
    cmd: "orchestrator.slash.sessionStart",
    detail: "New day / after eod-shutdown (not same-day mid-day return)",
  },
  {
    slash: "/chain session-resume",
    cmd: "orchestrator.slash.sessionResume",
    detail: "Same-day return after /chain session-end",
  },
  {
    slash: "/chain session-end",
    cmd: "orchestrator.slash.sessionEnd",
    detail: "Mid-day pause → next open is session-resume",
  },
  { slash: "/chain …", cmd: "orchestrator.slash.chain", detail: "Pick any registry chain → /chain <id>" },
  { slash: "/memory-brief", cmd: "orchestrator.slash.brief", detail: "Lean brief from SQLite (host helper)" },
  { slash: "/memory-query", cmd: "orchestrator.slash.query", detail: "Ask local memory" },
  { slash: "/memory-ingest", cmd: "orchestrator.slash.ingest", detail: "Save selection/text to memory" },
  { slash: "/memory-seed", cmd: "orchestrator.slash.seed", detail: "Seed VERSION/git/TODO" },
  { slash: "/memory-status", cmd: "orchestrator.slash.status", detail: "Memory + vault status" },
  { slash: "/memory-storage", cmd: "orchestrator.storage", detail: "Paths + dual-write report" },
  { slash: "/memory-serve", cmd: "orchestrator.memory.serve", detail: "Local HTTP + inbox watch" },
  { slash: "/setup", cmd: "orchestrator.slash.setup", detail: "Install host CLI + memory dirs" },
  { slash: "/quick-start", cmd: "orchestrator.quickStart", detail: "One-shot: install + seed + brief" },
  { slash: "/instructions", cmd: "orchestrator.readInstructions", detail: "Full memory + vault guide" },
  { slash: "/orchestrator-help", cmd: "orchestrator.slash.help", detail: "List all / commands" },
];

let outputChannel;
let statusBarItem;
/** @type {string} */
let lastBrief = "";
/** @type {string} */
let lastSlashPrompt = "";
/** @type {vscode.ExtensionContext | undefined} */
let extContext;

// ─── paths / CLI ─────────────────────────────────────────────────────────────

function cliBin() {
  const cfg = vscode.workspace.getConfiguration("orchestrator");
  return (cfg.get("cliPath") || "orchestrator").trim() || "orchestrator";
}

function publishedCliVersion() {
  const cfg = vscode.workspace.getConfiguration("orchestrator");
  return (cfg.get("publishedCliVersion") || DEFAULT_PUBLISHED_CLI).trim() || DEFAULT_PUBLISHED_CLI;
}

function scopeArgs() {
  const cfg = vscode.workspace.getConfiguration("orchestrator");
  const scope = cfg.get("memory.scope") || "project";
  return ["--scope", scope];
}

function workspaceRoot() {
  const f = vscode.workspace.workspaceFolders;
  if (!f || !f.length) {
    return process.cwd();
  }
  return f[0].uri.fsPath;
}

/** Project or global SQLite path (same contract as /memory-storage). */
function memoryDbPath() {
  const root = workspaceRoot();
  const scope =
    vscode.workspace.getConfiguration("orchestrator").get("memory.scope") || "project";
  if (scope === "global") {
    const home = process.env.ORCHESTRATOR_HOME || path.join(os.homedir(), ".orchestrator");
    return path.join(home, "memory", "memory.db");
  }
  return path.join(root, "reports", "memory", "memory.db");
}

/** Permanent $(database) item — visible on project open, not only after a command. */
function refreshStatusBar() {
  if (!statusBarItem) {
    return;
  }
  const cfg = vscode.workspace.getConfiguration("orchestrator");
  if (cfg.get("showStatusBar") === false) {
    statusBarItem.hide();
    return;
  }
  const dbPath = memoryDbPath();
  let present = false;
  try {
    present = fs.existsSync(dbPath);
  } catch (_) {
    present = false;
  }
  statusBarItem.text = "$(database) Memory";
  statusBarItem.tooltip = present
    ? `Orchestrator SQLite · ${dbPath} · click for hub`
    : `Orchestrator SQLite not created yet · ${dbPath} · click for hub or /memory-seed`;
  statusBarItem.command = "orchestrator.commandHub";
  statusBarItem.show();
}

function getChannel() {
  if (!outputChannel) {
    outputChannel = vscode.window.createOutputChannel("Orchestrator Memory");
  }
  return outputChannel;
}

function showOutput(title, text) {
  const ch = getChannel();
  ch.clear();
  ch.appendLine(`=== ${title} ===`);
  ch.appendLine(text || "(empty)");
  ch.show(true);
}

function shellQuote(s) {
  if (process.platform === "win32") {
    return `"${String(s).replace(/"/g, '\\"')}"`;
  }
  return `'${String(s).replace(/'/g, `'\\''`)}'`;
}

/**
 * @param {string[]} args
 * @param {{ cwd?: string, timeoutMs?: number }} [opts]
 */
function runCli(args, opts = {}) {
  const cwd = opts.cwd || workspaceRoot();
  const bin = cliBin();
  const timeoutMs = opts.timeoutMs || 120000;
  return new Promise((resolve, reject) => {
    const child = spawn(bin, args, {
      cwd,
      env: enrichPathEnv(process.env),
      shell: process.platform === "win32",
    });
    let out = "";
    let err = "";
    const timer = setTimeout(() => {
      try {
        child.kill("SIGTERM");
      } catch (_) {
        /* ignore */
      }
      reject(new Error(`Timed out after ${timeoutMs}ms: ${bin} ${args.join(" ")}`));
    }, timeoutMs);
    child.stdout.on("data", (d) => {
      out += d.toString();
    });
    child.stderr.on("data", (d) => {
      err += d.toString();
    });
    child.on("error", (e) => {
      clearTimeout(timer);
      reject(
        new Error(
          `Failed to spawn '${bin}': ${e.message}. Run /setup or /quick-start.`
        )
      );
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      if (code === 0) {
        resolve(out.trim());
      } else {
        reject(new Error((err || out || `exit ${code}`).trim()));
      }
    });
  });
}

function runMemory(args, opts = {}) {
  const cwd = opts.cwd || workspaceRoot();
  return runCli(["memory", ...scopeArgs(), "--path", cwd, ...args], opts);
}

/** Ensure ~/.local/bin is visible to spawned CLI (uv tool install location). */
function enrichPathEnv(env) {
  const e = { ...env };
  const home = os.homedir();
  const extras = [
    path.join(home, ".local", "bin"),
    path.join(home, ".cargo", "bin"),
  ];
  const cur = e.PATH || e.Path || "";
  const parts = cur.split(path.delimiter).filter(Boolean);
  for (const x of extras) {
    if (x && !parts.includes(x)) {
      parts.unshift(x);
    }
  }
  e.PATH = parts.join(path.delimiter);
  return e;
}

function candidateCliPaths() {
  const home = os.homedir();
  const bin = cliBin();
  const list = [];
  if (path.isAbsolute(bin)) {
    list.push(bin);
  }
  list.push(
    path.join(home, ".local", "bin", "orchestrator"),
    path.join(home, ".local", "bin", "orchestrator.exe")
  );
  return list;
}

function whichCli() {
  const bin = cliBin();
  if (path.isAbsolute(bin) && fs.existsSync(bin)) {
    return bin;
  }
  for (const p of candidateCliPaths()) {
    if (fs.existsSync(p)) {
      return p;
    }
  }
  const cmd = process.platform === "win32" ? "where" : "which";
  const r = spawnSync(cmd, [bin], {
    encoding: "utf8",
    shell: false,
    env: enrichPathEnv(process.env),
  });
  if (r.status === 0 && r.stdout) {
    return r.stdout.split(/\r?\n/).map((s) => s.trim()).filter(Boolean)[0] || null;
  }
  return null;
}

async function preferResolvedCliPath() {
  const found = whichCli();
  if (!found) {
    return null;
  }
  const cfg = vscode.workspace.getConfiguration("orchestrator");
  const current = (cfg.get("cliPath") || "orchestrator").trim();
  if (current === "orchestrator" && path.isAbsolute(found)) {
    try {
      await cfg.update("cliPath", found, vscode.ConfigurationTarget.Global);
    } catch (_) {
      /* ignore */
    }
  }
  return found;
}

async function memoryCliOk() {
  try {
    await preferResolvedCliPath();
    await runMemory(["status"]);
    return true;
  } catch (_) {
    return false;
  }
}

// ─── slash prompt builders (same text for IDE + models) ──────────────────────

/**
 * Canonical model / agent prompt. First line is always the real slash:
 *   /chain session-start
 * so Grok + Claude command lines and paste-into-model stay identical.
 */
function modelChainPrompt(chainId, name, brief) {
  const slash = `/chain ${chainId}`;
  const lines = [
    slash,
    "",
    `// Grok command line: type ${slash}`,
    `// Claude Code: type ${slash}`,
    `// Copilot / other: paste this block or type the same slash if the chain skill is installed`,
    "",
    `Chain: ${name || chainId}`,
    "Cache-first. Load manifest + lean cache before application source.",
    "Execute the chain skill with the id above (registry: chains/registry.yaml).",
    "",
  ];
  if (brief && brief.trim()) {
    lines.push("## Memory brief (optional host context)", "", brief.trim(), "");
  }
  lines.push(
    "After completion: summarize steps and cite cache files used.",
    "",
    "---",
    `Primary command (do not rename): ${slash}`
  );
  return lines.join("\n");
}

function modelSlashHelp() {
  return [
    "# Orchestrator slash commands",
    "",
    "## Grok + Claude command lines (canonical — type this)",
    "",
    "```text",
    "/chain session-start",
    "```",
    "",
    "That is the **same** command as today: Grok skill `chain` + Claude `.claude/commands/chain.md`.",
    "Also: `/chain session-resume` (same day) · `/chain eod-shutdown` · `/chain session-end` · `/chain delivery`",
    "",
    "## VS Code / Cursor extension (helpers — not a replacement)",
    "",
    "| Slash | What it does |",
    "|-------|----------------|",
    ...SLASH_CATALOG.map((s) => `| \`${s.slash}\` | ${s.detail} |`),
    "",
    "- **Command Palette:** `/chain` or helpers like `/memory-brief`",
    "- **Chat:** `@orchestrator /chain session-start`",
    "- **Paste for other models:** first line of `SESSION_READY.md` is always `/chain <id>`",
    "",
    "Do **not** invent alternate names for chains. Registry id after `/chain` is the command.",
  ].join("\n");
}

async function writeSessionFiles(chainId, brief, slashText) {
  const cfg = vscode.workspace.getConfiguration("orchestrator");
  if (cfg.get("writeSessionFiles") === false) {
    return [];
  }
  const root = workspaceRoot();
  const written = [];
  try {
    if (brief && brief.trim()) {
      const mem = path.join(root, "MEMORY.md");
      fs.writeFileSync(
        mem,
        `# MEMORY — Orchestrator Memory (local)\n\nGenerated by /memory-brief or /session-start. Free · Apache-2.0.\n\n---\n\n${brief.trim()}\n`,
        "utf8"
      );
      written.push(mem);
    }
    const ready = path.join(root, "SESSION_READY.md");
    const body = [
      `# SESSION_READY — /chain ${chainId}`,
      ``,
      `## Canonical command (Grok + Claude command lines)`,
      ``,
      "```text",
      `/chain ${chainId}`,
      "```",
      ``,
      `Type that **directly** in Grok or Claude (chain skill / \`.claude/commands/chain.md\`).`,
      `Do not rename it. Other chains: \`/chain eod-shutdown\`, \`/chain delivery\`, …`,
      ``,
      `## Full prompt (paste into models that have no /chain skill)`,
      ``,
      "```text",
      slashText.trim(),
      "```",
      ``,
      `## How to use`,
      ``,
      `- **Grok:** type \`/chain ${chainId}\` in the Grok command line`,
      `- **Claude Code:** type \`/chain ${chainId}\` in the Claude command line`,
      `- **VS Code Chat:** \`@orchestrator /chain ${chainId}\``,
      `- **Command Palette (extension):** \`/chain session-start\` or \`/chain …\``,
      ``,
    ].join("\n");
    fs.writeFileSync(ready, body, "utf8");
    written.push(ready);
  } catch (e) {
    getChannel().appendLine(`writeSessionFiles: ${e.message || e}`);
  }
  return written;
}

function ensureMemoryDirs() {
  const root = workspaceRoot();
  const dirs = [
    path.join(root, "reports", "memory"),
    path.join(root, "reports", "memory", "inbox"),
    path.join(root, "reports", "vault"),
  ];
  for (const d of dirs) {
    if (!fs.existsSync(d)) {
      fs.mkdirSync(d, { recursive: true });
    }
  }
  return dirs;
}

// ─── registry / chains ───────────────────────────────────────────────────────

function loadSlashCatalog(root) {
  /** Prefer generated multi-surface catalog when present. */
  const cat = path.join(root, "chains", "slash-catalog.yaml");
  if (!fs.existsSync(cat)) {
    return null;
  }
  const py = `
import json, sys
from pathlib import Path
try:
    import yaml
except ImportError:
    print("null")
    sys.exit(0)
data = yaml.safe_load(Path(${JSON.stringify(cat)}).read_text(encoding="utf-8")) or {}
skills = []
for s in data.get("skills") or []:
    if not isinstance(s, dict):
        continue
    slash = str(s.get("slash") or "")
    sid = str(s.get("id") or slash.lstrip("/"))
    skills.append({
        "id": sid,
        "slash": slash or ("/" + sid),
        "description": str(s.get("description") or "")[:160],
    })
chains = []
for c in data.get("chains") or []:
    if not isinstance(c, dict) or not c.get("id"):
        continue
    chains.append({
        "id": str(c.get("id")),
        "name": str(c.get("name") or c.get("id")),
        "description": str(c.get("description") or "")[:160],
    })
print(json.dumps({"chains": chains, "skills": skills, "canonical_session": data.get("canonical_session") or "/chain session-start"}))
`;
  const r = spawnSync("python3", ["-c", py], {
    encoding: "utf8",
    cwd: root,
    timeout: 15000,
    env: enrichPathEnv(process.env),
  });
  if (r.status === 0 && r.stdout && r.stdout.trim() !== "null") {
    try {
      return JSON.parse(r.stdout);
    } catch (_) {
      return null;
    }
  }
  return null;
}

function loadRegistry(root) {
  const fromCatalog = loadSlashCatalog(root);
  if (fromCatalog && (fromCatalog.skills.length || fromCatalog.chains.length)) {
    return fromCatalog;
  }
  const reg = path.join(root, "chains", "registry.yaml");
  const empty = { chains: [], skills: [] };
  if (!fs.existsSync(reg)) {
    return empty;
  }
  const py = `
import json, sys
from pathlib import Path
try:
    import yaml
except ImportError:
    print(json.dumps({"chains": [], "skills": [], "error": "no_yaml"}))
    sys.exit(0)
p = Path(${JSON.stringify(reg)})
data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
chains = []
for c in data.get("chains") or []:
    if not isinstance(c, dict) or not c.get("id"):
        continue
    chains.append({
        "id": str(c.get("id")),
        "name": str(c.get("name") or c.get("id")),
        "description": str(c.get("description") or c.get("summary") or "")[:160],
    })
skills = []
for s in data.get("skills") or []:
    if not isinstance(s, dict) or not s.get("id"):
        continue
    skills.append({
        "id": str(s.get("id")),
        "slash": str(s.get("slash") or ("/" + s.get("id"))),
        "description": str(s.get("description") or "")[:160],
    })
print(json.dumps({"chains": chains, "skills": skills}))
`;
  const r = spawnSync("python3", ["-c", py], {
    encoding: "utf8",
    cwd: root,
    timeout: 15000,
    env: enrichPathEnv(process.env),
  });
  if (r.status === 0 && r.stdout) {
    try {
      return JSON.parse(r.stdout);
    } catch (_) {
      /* fall through */
    }
  }
  try {
    const text = fs.readFileSync(reg, "utf8");
    const chains = [];
    const re = /^\s*-\s*id:\s*([a-zA-Z0-9._-]+)/gm;
    let m;
    const after = text.split(/\nchains:\s*\n/)[1] || text;
    while ((m = re.exec(after)) && chains.length < 200) {
      chains.push({ id: m[1], name: m[1], description: "" });
    }
    return { chains, skills: [] };
  } catch (_) {
    return empty;
  }
}

function allChains(root) {
  const reg = loadRegistry(root);
  const byId = new Map();
  for (const c of BUILTIN_CHAINS) {
    byId.set(c.id, c);
  }
  for (const c of reg.chains || []) {
    byId.set(c.id, c);
  }
  return Array.from(byId.values());
}

// ─── CLI install (one-click) ─────────────────────────────────────────────────

function uvInstallCommand() {
  const ver = publishedCliVersion();
  const url = `https://github.com/ndestates/orchestrator-memory/releases/download/v${ver}/orchestrator-${ver}-py3-none-any.whl`;
  return `uv tool install --force "orchestrator @ ${url}" && orchestrator version && orchestrator memory status`;
}

/**
 * Run install in an integrated terminal (user sees progress).
 * Also tries silent uv if available.
 */
async function installCliOneClick() {
  const ver = publishedCliVersion();
  const url = `https://github.com/ndestates/orchestrator-memory/releases/download/v${ver}/orchestrator-${ver}-py3-none-any.whl`;

  // Prefer silent uv when present
  const uv = spawnSync("uv", ["--version"], {
    encoding: "utf8",
    env: enrichPathEnv(process.env),
  });
  if (uv.status === 0) {
    const r = spawnSync(
      "uv",
      ["tool", "install", "--force", `orchestrator @ ${url}`],
      {
        encoding: "utf8",
        env: enrichPathEnv(process.env),
        timeout: 180000,
      }
    );
    getChannel().appendLine(r.stdout || "");
    getChannel().appendLine(r.stderr || "");
    if (r.status === 0) {
      await preferResolvedCliPath();
      if (await memoryCliOk()) {
        return { ok: true, method: "uv-silent" };
      }
    }
  }

  // Terminal fallback (user-visible)
  const term = vscode.window.createTerminal({
    name: "Orchestrator /setup",
    env: enrichPathEnv(process.env),
  });
  term.show();
  term.sendText(uvInstallCommand());
  vscode.window.showInformationMessage(
    "Terminal: installing host CLI via uv. When it finishes, run /session-start again."
  );
  return { ok: false, method: "terminal", pending: true };
}

async function ensureCliOrWizard(context) {
  if (await memoryCliOk()) {
    if (context && !context.globalState.get("orchestrator.instructionsAck")) {
      const cfg = vscode.workspace.getConfiguration("orchestrator");
      if (cfg.get("encourageReadInstructions") === true) {
        const pick = await vscode.window.showWarningMessage(
          "Optional: read /instructions once (SQLite + vault).",
          "Open /instructions",
          "I've read them",
          "Skip"
        );
        if (pick === "Open /instructions") {
          await cmdReadInstructions();
          return false;
        }
        if (pick === "I've read them") {
          await context.globalState.update("orchestrator.instructionsAck", true);
        }
      }
    }
    return true;
  }

  const pick = await vscode.window.showErrorMessage(
    "Host CLI missing or too old (need orchestrator memory). Install once — then all / commands work.",
    "/quick-start",
    "/setup",
    "Dismiss"
  );
  if (pick === "/quick-start") {
    await cmdQuickStart();
  } else if (pick === "/setup") {
    await cmdSetup();
  }
  return false;
}

// ─── storage helpers ─────────────────────────────────────────────────────────

function fileStats(p) {
  try {
    if (!fs.existsSync(p)) {
      return { exists: false, size: 0, lines: 0 };
    }
    const st = fs.statSync(p);
    let lines = 0;
    if (p.endsWith(".jsonl") || p.endsWith(".md")) {
      try {
        lines = fs.readFileSync(p, "utf8").split(/\r?\n/).filter((l) => l.trim()).length;
      } catch (_) {
        lines = 0;
      }
    }
    return { exists: true, size: st.size, lines, mtime: st.mtime.toISOString() };
  } catch (_) {
    return { exists: false, size: 0, lines: 0 };
  }
}

// ─── core command implementations ────────────────────────────────────────────

async function cmdReadInstructions() {
  const candidates = [
    path.join(__dirname, "INSTRUCTIONS.md"),
    path.join(workspaceRoot(), "extensions", "vscode-orchestrator", "INSTRUCTIONS.md"),
    path.join(__dirname, "README.md"),
  ];
  for (const p of candidates) {
    if (fs.existsSync(p)) {
      const doc = await vscode.workspace.openTextDocument(p);
      await vscode.window.showTextDocument(doc, { preview: false, viewColumn: vscode.ViewColumn.One });
      return;
    }
  }
  vscode.window.showErrorMessage("INSTRUCTIONS.md not found — reinstall the extension VSIX.");
}

async function cmdStorage() {
  const root = workspaceRoot();
  const scope =
    vscode.workspace.getConfiguration("orchestrator").get("memory.scope") || "project";
  const lines = [
    "Orchestrator Memory — storage",
    `Workspace: ${root}`,
    `Scope: ${scope}`,
    "Slash: /memory-storage",
    "",
  ];

  let dbPath = path.join(root, "reports", "memory", "memory.db");
  if (scope === "global") {
    const home = process.env.ORCHESTRATOR_HOME || path.join(os.homedir(), ".orchestrator");
    dbPath = path.join(home, "memory", "memory.db");
  }
  try {
    if (whichCli()) {
      const out = await runMemory(["db-path"]);
      if (out && out.trim()) {
        dbPath = out.trim().split(/\r?\n/).filter(Boolean).pop() || dbPath;
      }
    }
  } catch (_) {
    /* keep */
  }

  const vaultPath = path.join(root, "reports", "vault", "events.jsonl");
  const inboxDir = path.join(root, "reports", "memory", "inbox");
  const db = fileStats(dbPath);
  const vault = fileStats(vaultPath);

  lines.push(`SQLite: ${dbPath}  ${db.exists ? `PRESENT ${db.size}b` : "MISSING — run /memory-seed"}`);
  lines.push(`Vault:  ${vaultPath}  ${vault.exists ? `PRESENT ~${vault.lines} lines` : "MISSING"}`);
  lines.push(`Inbox:  ${inboxDir}  ${fs.existsSync(inboxDir) ? "PRESENT" : "MISSING"}`);
  lines.push("");

  try {
    if (whichCli()) {
      lines.push(await runMemory(["status"]));
    }
  } catch (e) {
    lines.push(String(e.message || e));
  }

  showOutput("/memory-storage", lines.join("\n"));
}

async function afterSlashReady(slashLabel, promptText, opts = {}) {
  lastSlashPrompt = promptText || "";
  await vscode.env.clipboard.writeText(lastSlashPrompt);
  showOutput(slashLabel, lastSlashPrompt);

  const actions = ["Open SESSION_READY.md", "Copy again", "Chat tip", "OK"];
  const pick = await vscode.window.showInformationMessage(
    `${slashLabel} ready — copied. Paste into any model, or open SESSION_READY.md.`,
    ...actions
  );
  if (pick === "Open SESSION_READY.md") {
    const p = path.join(workspaceRoot(), "SESSION_READY.md");
    if (fs.existsSync(p)) {
      const doc = await vscode.workspace.openTextDocument(p);
      await vscode.window.showTextDocument(doc);
    }
  } else if (pick === "Copy again") {
    await vscode.env.clipboard.writeText(lastSlashPrompt);
  } else if (pick === "Chat tip") {
    vscode.window.showInformationMessage(
      "VS Code Chat: type @orchestrator /session-start   ·   Models: paste /chain session-start"
    );
  }
  if (opts.openChatTip) {
    /* reserved */
  }
}

async function buildBrief() {
  ensureMemoryDirs();
  const text = await runMemory(["brief", "--seed"]);
  lastBrief = text;
  return text;
}

async function cmdSessionStart() {
  if (!(await ensureCliOrWizard(extContext))) {
    return;
  }
  try {
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: "/chain session-start — seeding memory + brief…",
      },
      async () => {
        ensureMemoryDirs();
        try {
          await runMemory(["seed"]);
        } catch (_) {
          /* seed optional if empty project */
        }
        const brief = await buildBrief();
        const prompt = modelChainPrompt("session-start", "Session start", brief);
        await writeSessionFiles("session-start", brief, prompt);
        // Canonical slash for Grok/Claude is /chain session-start (not a new name)
        await afterSlashReady("/chain session-start", prompt);
      }
    );
  } catch (e) {
    vscode.window.showErrorMessage(String(e.message || e));
  }
}

async function cmdSessionResume() {
  if (!(await ensureCliOrWizard(extContext))) {
    return;
  }
  try {
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: "/chain session-resume — same-day return…",
      },
      async () => {
        const brief = await buildBrief().catch(() => lastBrief || "");
        const prompt = modelChainPrompt(
          "session-resume",
          "Session resume (same day after session-end)",
          brief
        );
        await writeSessionFiles("session-resume", brief, prompt);
        await afterSlashReady("/chain session-resume", prompt);
      }
    );
  } catch (e) {
    vscode.window.showErrorMessage(String(e.message || e));
  }
}

async function cmdSessionEnd() {
  if (!(await ensureCliOrWizard(extContext))) {
    return;
  }
  try {
    const brief = await buildBrief().catch(() => lastBrief || "");
    const prompt = modelChainPrompt(
      "session-end",
      "Session end (mid-day) — next: /chain session-resume",
      brief
    );
    await writeSessionFiles("session-end", brief, prompt);
    await afterSlashReady("/chain session-end", prompt);
  } catch (e) {
    vscode.window.showErrorMessage(String(e.message || e));
  }
}

async function cmdBrief() {
  if (!(await ensureCliOrWizard(extContext))) {
    return;
  }
  try {
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: "/memory-brief …",
      },
      async () => {
        const text = await buildBrief();
        showOutput("/memory-brief", text);
        await vscode.env.clipboard.writeText(text);
        const written = await writeSessionFiles("session-start", text, modelChainPrompt("session-start", "Session start", text));
        const pick = await vscode.window.showInformationMessage(
          "/memory-brief copied. Use with any model, or continue to /session-start.",
          "Copy for Claude",
          "Copy for Cursor",
          "Copy for Copilot",
          "/session-start",
          "Open MEMORY.md"
        );
        if (pick === "Copy for Claude") {
          await vscode.env.clipboard.writeText(
            `# Project memory brief\n\nUse as session context.\n\n${text}`
          );
        } else if (pick === "Copy for Cursor") {
          await vscode.env.clipboard.writeText(`# Cursor context\n\n${text}\n`);
        } else if (pick === "Copy for Copilot") {
          await vscode.env.clipboard.writeText(`Project memory brief:\n\n${text}`);
        } else if (pick === "/session-start") {
          await cmdSessionStart();
        } else if (pick === "Open MEMORY.md" && written[0]) {
          const doc = await vscode.workspace.openTextDocument(written[0]);
          await vscode.window.showTextDocument(doc);
        }
      }
    );
  } catch (e) {
    vscode.window.showErrorMessage(String(e.message || e));
  }
}

async function cmdStatus() {
  if (!(await ensureCliOrWizard(extContext))) {
    return;
  }
  try {
    const text = await runMemory(["status"]);
    const vaultPath = path.join(workspaceRoot(), "reports", "vault", "events.jsonl");
    const vault = fileStats(vaultPath);
    showOutput(
      "/memory-status",
      [
        text,
        "",
        "--- vault ---",
        vault.exists ? `PRESENT ${vaultPath}` : `MISSING ${vaultPath}`,
      ].join("\n")
    );
  } catch (e) {
    vscode.window.showErrorMessage(String(e.message || e));
  }
}

async function cmdSeed() {
  if (!(await ensureCliOrWizard(extContext))) {
    return;
  }
  try {
    ensureMemoryDirs();
    const text = await runMemory(["seed"]);
    showOutput("/memory-seed", text);
    vscode.window.showInformationMessage("/memory-seed done — situation in SQLite");
  } catch (e) {
    vscode.window.showErrorMessage(String(e.message || e));
  }
}

async function cmdQuery(prefill) {
  if (!(await ensureCliOrWizard(extContext))) {
    return;
  }
  const q =
    (typeof prefill === "string" && prefill.trim()) ||
    (await vscode.window.showInputBox({
      prompt: "/memory-query — ask local project memory",
      placeHolder: "What is open? / auth flow / open TODOs",
    }));
  if (!q) {
    return;
  }
  try {
    const text = await runMemory(["query", q]);
    showOutput("/memory-query", text);
    await vscode.env.clipboard.writeText(text);
  } catch (e) {
    vscode.window.showErrorMessage(String(e.message || e));
  }
}

async function cmdIngest(prefill) {
  if (!(await ensureCliOrWizard(extContext))) {
    return;
  }
  const editor = vscode.window.activeTextEditor;
  let text = typeof prefill === "string" ? prefill : "";
  if (!text.trim()) {
    if (editor && !editor.selection.isEmpty) {
      text = editor.document.getText(editor.selection);
    } else if (editor) {
      text = editor.document.getText();
    }
  }
  if (!text || !text.trim()) {
    text = await vscode.window.showInputBox({
      prompt: "/memory-ingest — text to save into local memory DB",
    });
  }
  if (!text || !text.trim()) {
    return;
  }
  try {
    const source = editor
      ? path.basename(editor.document.fileName || "editor")
      : "vscode";
    const out = await runMemory([
      "ingest",
      "--text",
      text.slice(0, 12000),
      "--source",
      source,
    ]);
    showOutput("/memory-ingest", out);
    vscode.window.showInformationMessage("/memory-ingest saved to SQLite (vault dual-write when available)");
  } catch (e) {
    vscode.window.showErrorMessage(String(e.message || e));
  }
}

async function cmdServe() {
  if (!(await ensureCliOrWizard(extContext))) {
    return;
  }
  const cfg = vscode.workspace.getConfiguration("orchestrator");
  const port = cfg.get("memory.servePort") || 8888;
  const cwd = workspaceRoot();
  const bin = whichCli() || cliBin();
  const scope = cfg.get("memory.scope") || "project";
  const term = vscode.window.createTerminal({
    name: "/memory-serve",
    cwd,
    env: enrichPathEnv(process.env),
  });
  term.sendText(
    `${shellQuote(bin)} memory --scope ${scope} --path ${shellQuote(cwd)} serve --port ${port}`
  );
  term.show();
  vscode.window.showInformationMessage(`/memory-serve on port ${port} (local only)`);
}

async function cmdSetup() {
  const found = whichCli();
  const lines = [
    "/setup — Orchestrator host CLI",
    `Configured: ${cliBin()}`,
    `Resolved: ${found || "(not found)"}`,
    `Published wheel target: v${publishedCliVersion()}`,
    "",
  ];
  let memoryOk = false;
  if (found) {
    try {
      lines.push(await runCli(["version"]), "");
    } catch (e) {
      lines.push(String(e.message || e), "");
    }
    memoryOk = await memoryCliOk();
    lines.push(memoryOk ? "memory: OK" : "memory: FAILED — need 2.0.0+");
  } else {
    lines.push("CLI missing. One-click uses uv + GitHub Release wheel.", "", uvInstallCommand());
  }
  showOutput("/setup", lines.join("\n"));

  if (memoryOk) {
    ensureMemoryDirs();
    vscode.window.showInformationMessage(
      "CLI ready. Type /session-start in the Command Palette, or @orchestrator /session-start in Chat."
    );
    return;
  }

  const act = await vscode.window.showWarningMessage(
    "Install host CLI so /session-start and /memory-* work.",
    "Install now (uv)",
    "Copy install command",
    "Open terminal"
  );
  if (act === "Install now (uv)") {
    const res = await installCliOneClick();
    if (res.ok) {
      ensureMemoryDirs();
      vscode.window.showInformationMessage("Installed. Run /session-start.");
    }
  } else if (act === "Copy install command") {
    await vscode.env.clipboard.writeText(uvInstallCommand());
    vscode.window.showInformationMessage("Install command copied — paste in a terminal");
  } else if (act === "Open terminal") {
    const term = vscode.window.createTerminal({
      name: "Orchestrator /setup",
      env: enrichPathEnv(process.env),
    });
    term.show();
    term.sendText(uvInstallCommand());
  }
}

async function cmdQuickStart() {
  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: "/quick-start — CLI + memory + brief…",
    },
    async () => {
      ensureMemoryDirs();
      let ok = await memoryCliOk();
      if (!ok) {
        const res = await installCliOneClick();
        if (res.ok) {
          ok = true;
        } else if (res.pending) {
          vscode.window.showWarningMessage(
            "Finish install in the terminal, then run /quick-start again."
          );
          return;
        }
      }
      if (!ok) {
        vscode.window.showErrorMessage(
          "CLI still missing. Install uv (https://docs.astral.sh/uv/) then /setup."
        );
        return;
      }
      try {
        await runMemory(["seed"]).catch(() => "");
        const brief = await buildBrief();
        const prompt = modelChainPrompt("session-start", "Session start", brief);
        await writeSessionFiles("session-start", brief, prompt);
        await afterSlashReady("/quick-start → /session-start", prompt);
        if (extContext) {
          await extContext.globalState.update("orchestrator.instructionsAck", true);
        }
      } catch (e) {
        vscode.window.showErrorMessage(String(e.message || e));
      }
    }
  );
}

async function cmdOpenDocs() {
  await cmdReadInstructions();
}

async function cmdSlashHelp() {
  const text = modelSlashHelp();
  showOutput("/orchestrator-help", text);
  await vscode.env.clipboard.writeText(text);
  const doc = await vscode.workspace.openTextDocument({
    content: text,
    language: "markdown",
  });
  await vscode.window.showTextDocument(doc, { preview: true });
  vscode.window.showInformationMessage("Slash command list opened + copied");
}

async function cmdSlashHub() {
  const items = SLASH_CATALOG.map((s) => ({
    label: s.slash,
    description: s.detail,
    cmd: s.cmd,
  }));
  const pick = await vscode.window.showQuickPick(items, {
    title: "Orchestrator / commands (same text in models)",
    placeHolder: "Type /session-start · /chain · /memory-brief …",
    matchOnDescription: true,
  });
  if (pick) {
    await vscode.commands.executeCommand(pick.cmd);
  }
}

async function cmdCommandHub() {
  await cmdSlashHub();
}

/**
 * @param {string} [presetId]
 */
async function cmdRunChain(presetId) {
  const root = workspaceRoot();
  const chains = allChains(root);

  let chainId = typeof presetId === "string" ? presetId : "";
  if (!chainId) {
    const items = chains.map((c) => ({
      label: `/chain ${c.id}`,
      description: c.name,
      detail: c.description,
      id: c.id,
      name: c.name,
    }));
    const pin = [
      "session-start",
      "session-resume",
      "session-end",
      "always-on-memory",
      "delivery",
      "code-review",
    ];
    items.sort((a, b) => {
      const ia = pin.indexOf(a.id);
      const ib = pin.indexOf(b.id);
      if (ia >= 0 || ib >= 0) {
        return (ia < 0 ? 999 : ia) - (ib < 0 ? 999 : ib);
      }
      return a.label.localeCompare(b.label);
    });
    const pick = await vscode.window.showQuickPick(items, {
      title: "/chain — pick a chain (same / text for every model)",
      placeHolder: "/chain session-start",
      matchOnDescription: true,
      matchOnDetail: true,
    });
    if (!pick) {
      return;
    }
    chainId = pick.id;
  }

  const meta = chains.find((c) => c.id === chainId) || { id: chainId, name: chainId };
  let brief = lastBrief;
  if (await memoryCliOk()) {
    try {
      brief = await buildBrief();
    } catch (_) {
      /* optional */
    }
  }
  const prompt = modelChainPrompt(chainId, meta.name, brief);
  await writeSessionFiles(chainId, brief, prompt);
  await afterSlashReady(`/chain ${chainId}`, prompt);
}

async function cmdRunSkill() {
  const root = workspaceRoot();
  const reg = loadRegistry(root);
  const fallback = [
    { id: "session-start", slash: "/session-start", description: "New day / after eod" },
    { id: "session-resume", slash: "/session-resume", description: "Same-day after session-end" },
    { id: "chain", slash: "/chain", description: "Named chain" },
    { id: "daily-standup", slash: "/daily-standup", description: "Daily standup" },
    { id: "always-on-memory", slash: "/always-on-memory", description: "Memory skill" },
    { id: "load-cache", slash: "/load-cache", description: "Load project cache" },
    { id: "code-review", slash: "/code-review", description: "Diff review" },
  ];
  const skills = reg.skills.length ? reg.skills : fallback;
  const items = skills.map((s) => ({
    label: s.slash || `/${s.id}`,
    description: s.id,
    detail: s.description,
    slash: s.slash || `/${s.id}`,
  }));
  const pick = await vscode.window.showQuickPick(items, {
    title: "Skill / command — copies slash for models",
    placeHolder: "/session-start · /chain · /daily-standup …",
    matchOnDescription: true,
    matchOnDetail: true,
  });
  if (!pick) {
    return;
  }
  let extra = "";
  if (pick.slash === "/chain") {
    const arg = await vscode.window.showInputBox({
      prompt: "Chain id",
      placeHolder: "session-start",
      value: "session-start",
    });
    if (arg) {
      extra = ` ${arg.trim()}`;
    }
  }
  const text = `${pick.slash}${extra}`;
  await vscode.env.clipboard.writeText(text);
  showOutput(pick.slash, text);
  vscode.window.showInformationMessage(`Copied ${text} — paste into any model`);
}

async function cmdCopyBrief() {
  if (!lastBrief.trim()) {
    const run = await vscode.window.showInformationMessage("No brief yet.", "/memory-brief");
    if (run === "/memory-brief") {
      await cmdBrief();
    }
    return;
  }
  await vscode.env.clipboard.writeText(lastBrief);
  vscode.window.showInformationMessage("Last /memory-brief copied");
}

async function cmdExportBrief() {
  if (!lastBrief.trim()) {
    try {
      await buildBrief();
    } catch (e) {
      vscode.window.showErrorMessage(String(e.message || e));
      return;
    }
  }
  await writeSessionFiles("session-start", lastBrief, modelChainPrompt("session-start", "Session start", lastBrief));
  const dest = path.join(workspaceRoot(), "MEMORY.md");
  if (fs.existsSync(dest)) {
    const doc = await vscode.workspace.openTextDocument(dest);
    await vscode.window.showTextDocument(doc);
  }
}

// ─── Chat participant (@orchestrator /session-start) ─────────────────────────

/**
 * @param {import('vscode').ChatRequest} request
 * @param {import('vscode').ChatContext} _context
 * @param {import('vscode').ChatResponseStream} stream
 * @param {import('vscode').CancellationToken} _token
 */
async function handleChatRequest(request, _context, stream, _token) {
  const command = (request.command || "").replace(/^\//, "");
  const userText = (request.prompt || "").trim();

  stream.progress("Orchestrator…");

  try {
    if (!command || command === "help") {
      stream.markdown(modelSlashHelp());
      stream.markdown(
        "\n\nIn **this chat** try: `/session-start`, `/brief`, `/chain session-start`, `/query what is open?`, `/setup`\n"
      );
      return { metadata: { command: "help" } };
    }

    if (command === "setup") {
      stream.markdown("## /setup\n\nInstalling or checking host CLI…\n");
      const ok = await memoryCliOk();
      if (ok) {
        ensureMemoryDirs();
        const ver = await runCli(["version"]).catch(() => "ok");
        stream.markdown(`CLI ready:\n\n\`\`\`\n${ver}\n\`\`\`\n\nNext: \`/session-start\`\n`);
      } else {
        const res = await installCliOneClick();
        if (res.ok) {
          stream.markdown("Host CLI installed via **uv**. Run `/session-start`.\n");
        } else {
          stream.markdown(
            "Could not install silently. A terminal was opened — run the install, then `/session-start`.\n\n" +
              "```bash\n" +
              uvInstallCommand() +
              "\n```\n"
          );
        }
      }
      return { metadata: { command: "setup" } };
    }

    if (command === "status") {
      if (!(await memoryCliOk())) {
        stream.markdown("CLI missing. Run `@orchestrator /setup` first.\n");
        return { metadata: { command: "status", error: "no-cli" } };
      }
      const text = await runMemory(["status"]);
      stream.markdown("## /memory-status\n\n```\n" + text + "\n```\n");
      return { metadata: { command: "status" } };
    }

    if (command === "seed") {
      if (!(await memoryCliOk())) {
        stream.markdown("CLI missing. Run `@orchestrator /setup` first.\n");
        return { metadata: { command: "seed", error: "no-cli" } };
      }
      ensureMemoryDirs();
      const text = await runMemory(["seed"]);
      stream.markdown("## /memory-seed\n\n```\n" + text + "\n```\n");
      return { metadata: { command: "seed" } };
    }

    if (command === "brief") {
      if (!(await memoryCliOk())) {
        stream.markdown("CLI missing. Run `@orchestrator /setup` first.\n");
        return { metadata: { command: "brief", error: "no-cli" } };
      }
      const brief = await buildBrief();
      stream.markdown("## /memory-brief\n\n" + brief + "\n");
      await writeSessionFiles("session-start", brief, modelChainPrompt("session-start", "Session start", brief));
      stream.markdown("\n_Also wrote `MEMORY.md` / `SESSION_READY.md` when enabled._\n");
      return { metadata: { command: "brief" } };
    }

    if (command === "query") {
      if (!(await memoryCliOk())) {
        stream.markdown("CLI missing. Run `@orchestrator /setup` first.\n");
        return { metadata: { command: "query", error: "no-cli" } };
      }
      const q = userText || "What is open next?";
      const text = await runMemory(["query", q]);
      stream.markdown(`## /memory-query\n\n**Q:** ${q}\n\n${text}\n`);
      return { metadata: { command: "query" } };
    }

    if (command === "ingest") {
      if (!(await memoryCliOk())) {
        stream.markdown("CLI missing. Run `@orchestrator /setup` first.\n");
        return { metadata: { command: "ingest", error: "no-cli" } };
      }
      if (!userText) {
        stream.markdown("Usage: `@orchestrator /ingest your note here`\n");
        return { metadata: { command: "ingest", error: "no-text" } };
      }
      const out = await runMemory([
        "ingest",
        "--text",
        userText.slice(0, 12000),
        "--source",
        "chat",
      ]);
      stream.markdown("## /memory-ingest\n\n```\n" + out + "\n```\n");
      return { metadata: { command: "ingest" } };
    }

    if (
      command === "session-start" ||
      command === "session-resume" ||
      command === "session-end" ||
      command === "chain"
    ) {
      if (!(await memoryCliOk())) {
        stream.markdown("CLI missing. Run `@orchestrator /setup` first.\n");
        return { metadata: { command, error: "no-cli" } };
      }
      let chainId = "session-start";
      if (command === "session-resume") {
        chainId = "session-resume";
      } else if (command === "session-end") {
        chainId = "session-end";
      } else if (command === "chain") {
        chainId = (userText.split(/\s+/)[0] || "session-start").trim();
      }
      ensureMemoryDirs();
      try {
        await runMemory(["seed"]);
      } catch (_) {
        /* optional */
      }
      const brief = await buildBrief();
      const meta = allChains(workspaceRoot()).find((c) => c.id === chainId);
      const prompt = modelChainPrompt(chainId, meta ? meta.name : chainId, brief);
      await writeSessionFiles(chainId, brief, prompt);

      stream.markdown(`## \`/chain ${chainId}\`\n\n`);
      stream.markdown(
        "Use the following as the **model instruction** (also copied-ready via `SESSION_READY.md`):\n\n"
      );
      stream.markdown("```text\n" + prompt + "\n```\n");
      stream.markdown(
        "\n**Continue in this chat:** treat the block above as your system task and execute `/chain " +
          chainId +
          "` for this workspace.\n"
      );
      lastSlashPrompt = prompt;
      lastBrief = brief;
      return { metadata: { command, chainId } };
    }

    // Unknown: treat free text as query or show help
    if (userText) {
      if (await memoryCliOk()) {
        const text = await runMemory(["query", userText]);
        stream.markdown(`## Memory\n\n**Q:** ${userText}\n\n${text}\n`);
        return { metadata: { command: "free-query" } };
      }
    }
    stream.markdown(modelSlashHelp());
    return { metadata: { command: "help" } };
  } catch (e) {
    stream.markdown(`**Error:** ${e.message || e}\n\nTry \`@orchestrator /setup\`.\n`);
    return { metadata: { error: String(e.message || e) } };
  }
}

function registerChatParticipant(context) {
  if (!vscode.chat || typeof vscode.chat.createChatParticipant !== "function") {
    getChannel().appendLine(
      "vscode.chat API unavailable — slash commands still work in Command Palette."
    );
    return;
  }
  try {
    const participant = vscode.chat.createChatParticipant(
      "orchestrator.memory",
      handleChatRequest
    );
    participant.iconPath = vscode.Uri.file(path.join(__dirname, "media", "icon.png"));
    if (participant.followupProvider) {
      /* optional */
    }
    // Follow-ups
    participant.followupProvider = {
      provideFollowups() {
        return [
          { prompt: "/session-start", label: "/session-start", command: "session-start" },
          { prompt: "/brief", label: "/memory-brief", command: "brief" },
          { prompt: "/help", label: "Help", command: "help" },
        ];
      },
    };
    context.subscriptions.push(participant);
    getChannel().appendLine("Chat participant @orchestrator registered (slash: /session-start, /chain, …)");
  } catch (e) {
    getChannel().appendLine(`Chat participant failed: ${e.message || e}`);
  }
}

// ─── activate ────────────────────────────────────────────────────────────────

/**
 * Activates when a project window finishes starting (`onStartupFinished`) so
 * the SQLite $(database) status item is visible immediately, and also via
 * Command Palette / Chat @orchestrator.
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
  extContext = context;
  getChannel().appendLine(
    "Orchestrator Memory activated (project open — SQLite status bar)."
  );

  const cfg = vscode.workspace.getConfiguration("orchestrator");
  if (cfg.get("showStatusBar") !== false) {
    statusBarItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Left,
      100
    );
    refreshStatusBar();
    context.subscriptions.push(statusBarItem);

    const dbWatch = vscode.workspace.createFileSystemWatcher(
      new vscode.RelativePattern(workspaceRoot(), "reports/memory/memory.db")
    );
    dbWatch.onDidCreate(() => refreshStatusBar());
    dbWatch.onDidDelete(() => refreshStatusBar());
    dbWatch.onDidChange(() => refreshStatusBar());
    context.subscriptions.push(dbWatch);
    context.subscriptions.push(
      vscode.workspace.onDidChangeWorkspaceFolders(() => refreshStatusBar())
    );
    context.subscriptions.push(
      vscode.workspace.onDidChangeConfiguration((e) => {
        if (
          e.affectsConfiguration("orchestrator.showStatusBar") ||
          e.affectsConfiguration("orchestrator.memory.scope")
        ) {
          refreshStatusBar();
        }
      })
    );
  }

  const regs = [
    ["orchestrator.slash.sessionStart", cmdSessionStart],
    ["orchestrator.slash.sessionResume", cmdSessionResume],
    ["orchestrator.slash.sessionEnd", cmdSessionEnd],
    ["orchestrator.slash.brief", cmdBrief],
    ["orchestrator.slash.query", () => cmdQuery()],
    ["orchestrator.slash.ingest", () => cmdIngest()],
    ["orchestrator.slash.seed", cmdSeed],
    ["orchestrator.slash.status", cmdStatus],
    ["orchestrator.slash.chain", () => cmdRunChain()],
    ["orchestrator.slash.setup", cmdSetup],
    ["orchestrator.slash.help", cmdSlashHelp],
    ["orchestrator.slashHub", cmdSlashHub],
    ["orchestrator.quickStart", cmdQuickStart],
    ["orchestrator.memory.brief", cmdBrief],
    ["orchestrator.memory.status", cmdStatus],
    ["orchestrator.memory.seed", cmdSeed],
    ["orchestrator.memory.query", () => cmdQuery()],
    ["orchestrator.memory.ingest", () => cmdIngest()],
    ["orchestrator.memory.serve", cmdServe],
    ["orchestrator.setup", cmdSetup],
    ["orchestrator.openDocs", cmdOpenDocs],
    ["orchestrator.readInstructions", cmdReadInstructions],
    ["orchestrator.storage", cmdStorage],
    ["orchestrator.commandHub", cmdCommandHub],
    ["orchestrator.runChain", cmdRunChain],
    ["orchestrator.runSkill", cmdRunSkill],
    ["orchestrator.copyBrief", cmdCopyBrief],
    ["orchestrator.exportBrief", cmdExportBrief],
  ];
  for (const [id, fn] of regs) {
    context.subscriptions.push(vscode.commands.registerCommand(id, fn));
  }

  registerChatParticipant(context);

  // Optional one-time tip only if user enabled the setting (never on window open alone —
  // activate already required a command or Chat).
  const key = "orchestrator.memory.welcomed.v2";
  if (
    cfg.get("showWelcomeOnActivate") === true &&
    !context.workspaceState.get(key)
  ) {
    context.workspaceState.update(key, true);
    void vscode.window
      .showInformationMessage(
        "Orchestrator is ready. Palette: /chain session-start · Chat: @orchestrator /session-start",
        "/quick-start",
        "OK"
      )
      .then(async (pick) => {
        if (pick === "/quick-start") {
          await cmdQuickStart();
        }
      });
  }
}

function deactivate() {
  if (outputChannel) {
    outputChannel.dispose();
  }
  if (statusBarItem) {
    statusBarItem.dispose();
  }
}

module.exports = { activate, deactivate };
