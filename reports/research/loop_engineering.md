# Loop Engineering: The 14-Step Roadmap from Prompter to Loop Designer

**Source (primary):** [@0xCodez on X](https://x.com/0xCodez/status/2064374643729773029) — Jun 9, 2026  
**Source (article mirror):** [Medium — Neyzis / Coinmonks](https://medium.com/coinmonks/loop-engineering-the-14-step-roadmap-from-prompter-to-loop-designer-bda3edc46fbc) — Jun 15, 2026  
**Related:** [Addy Osmani — Loop Engineering](https://addyosmani.com/blog/loop-engineering/) (cited throughout the article)

> Most developers still prompt their coding agents by hand. They type, they wait, they read the diff, and they type again. In fact, 9 out of 10 builders have never written a single loop that prompts the agent for them.

Without automation, state files, verifiers, or automated schedules, you are missing the biggest shift in AI development. The leverage point has officially moved — from typing prompts to designing systems that prompt.

This is the 14-step roadmap to make that shift, sourced from Anthropic engineering docs, Addy Osmani’s deep dives on loop engineering, and recent measurement studies.

**14 steps. 3 tiers. Stop prompting. Start designing.**

**In this guide, you’ll discover:**

- ✅ **The 4-condition test** to know if you actually need a loop.
- ✅ **The 5 essential building blocks** (automations, worktrees, skills, connectors, sub-agents).
- ✅ **The “Ralph Wiggum” failure mode** and how to avoid it.
- ✅ **Comprehension debt** — the hidden cost of fast automation.
- ✅ **The security tax** of unattended loops.
- ✅ **The minimum viable loop architecture**.

---

## PART 1 · The Why & The Test

### 01. Loop Engineering is Replacing Yourself as the Prompter

For the last two years, getting value out of a coding agent followed a predictable pattern: write a prompt, share the context, review the output, and write the next prompt. The agent was a tool, and you held it the entire time. That phase is ending.

Loop engineering is the practice of building a small system that finds the work, hands it to the agent, checks the result, records the outcome, and decides the next move — entirely on its own. You design the system once, and the system prompts the agent from then on.

> **The Productivity Shift**
>
> Anthropic engineers now merge eight times as much code per day as they did in 2024. While Anthropic itself notes this figure is “almost certainly an overstatement of true productivity gains,” the underlying mechanism is undeniable: leverage moves exponentially when you stop typing prompts and start designing the loops that generate them.

### 02. Run the 4-Condition Test Before You Build Anything

Loops earn their keep under very specific circumstances. Miss just one condition, and your loop will cost far more than it returns. A loop only makes sense if it passes these four tests:

- **The Task Repeats:** A loop amortizes its setup cost across many runs. For a one-time job, writing a solid manual prompt remains faster and cheaper. If the work doesn’t recur weekly, you don’t have a loop; you have a script.
- **Verification is Automated:** The loop requires an objective gatekeeper that can reject bad code without a human in the room. This means a test suite, a type checker, a linter, or a successful build. Without an automated check, you are stuck back in your chair reading every single diff, defeating the entire purpose of the automation.
- **Your Token Budget Can Absorb the Waste:** Loops are inherently exploratory. They re-read massive contexts, retry failed approaches, and explore alternative paths. This burns tokens rapidly whether the run ships code or not. The technique scales beautifully with an enterprise budget, but it can look reckless on a strictly metered, personal plan.
- **The Agent Has Senior Tools:** The agent cannot iterate blindly. It needs logs, a reproduction environment, and the ability to run the code it just wrote to see exactly what breaks.

### 03. Who Wins, Who Loses (The Economics of Loops)

The economics of loop engineering are not universal. The builders calling loops “obvious” typically enjoy unmetered enterprise API access. The people calling it “reckless” are usually solo developers on a $20 consumer plan trying to run heavy verification loops while dodging surprise invoices.

**Who benefits in practice:**

- **Codebases with strong test coverage:** If a task could be handled by a junior engineer using a checklist, and your test suite is strong enough to catch their mistakes, a loop fits perfectly.
- **Repetitive, machine-checkable routines:** Continuous test triage, automated dependency updates, lint-and-fix passes, and converting clean issue descriptions into draft PRs.
- **Async-first teams:** Engineering organizations already leveraging multi-agent patterns where routines serve as the missing orchestration layer.

**Who should skip it:**

- **Solo builders on consumer plans:** The token bill will almost certainly arrive before the productivity gains do.
- **Codebases without automated tests:** A loop running without a strict validation gate is just an agent agreeing with itself on repeat.
- **Teams bottlenecked by code review:** A loop will generate code faster, but if human review is already your main constraint, you are simply piling more work into an already jammed queue.

### 04. The 30-Second Loop Check

While the 4-condition test handles your high-level strategy, this tactical checklist is what you run on a specific task before turning it over to a loop. If you can’t check every box, keep it as a manual prompt.

- [ ] The task occurs at least once a week.
- [ ] A test, type check, build, or linter can instantly reject bad output.
- [ ] The agent has a live environment to run and test its changes.
- [ ] The loop has an absolute hard stop (token cap, timeout, or iteration limit).
- [ ] A human approval gate exists before any merge or production deployment.

**Good first loops:**

- **CI failure triage:** Scanning nightly build failures, classifying causes, and drafting fix PRs for minor bugs.
- **Dependency maintenance:** Weekly compatibility scans and automated version bump PRs.
- **Lint-and-fix passes:** Automatically correcting style violations on every PR open event.

**Bad first loops (keep a human in the chair):**

- Architectural overhauls or refactoring core systems.
- Authentication, cryptography, or payments code.
- Production deployments and vague product feature work where “done” is a subjective judgment call.

---

## PART 2 · The 5 Building Blocks

### 05. Automations: The Heartbeat

Automations turn a single manual run into an ongoing system. They trigger based on a schedule, a repository event, or a specific condition. They act as the heartbeat of your loop; everything else hangs off them.

Modern developer environments approach this through specific primitives:

- **Cadence loops (`/loop`):** Runs on a fixed time interval or session-scoped cadence. Use this for regular system health and quality checks regardless of state.
- **Goal-driven triggers (`/goal`):** Keeps executing until a specific condition is explicitly true. Crucially, a separate, smaller model handles the completion check. This enforces a **maker-vs-checker split** right at the stop condition, ensuring the agent that wrote the code isn't the one grading its own success.

Example:

```text
/loop 30m /goal All tests in test/auth pass and lint is clean.
Scan src/auth for new failures, propose fixes in claude/auth-fixes,
open draft PR when goal holds.
```

### 06. Worktrees: Parallel Without Chaos

The moment you run multiple agents simultaneously, files collide. Two agents writing to the same file causes the exact same merge conflicts as two engineers committing to the exact same lines without syncing.

The solution is a **Git worktree** — a separate working directory on its own isolated branch that shares the same repository history.

By utilizing isolation flags (like `--worktree`), subagents get a clean checkout that automatically removes itself after execution. Worktrees eliminate mechanical file collisions, but remember: your own review bandwidth remains the ultimate ceiling on how many parallel loops you should run.

### 07. Skills: Write Once, Read on Every Run

A *Skill* prevents your loop from acting like a goldfish that has to re-learn your entire project context every single session. Skills are structured as dedicated directories containing a `SKILL.md` file alongside necessary helper scripts, references, and assets.

Without skills, a loop wastes immense token volume re-deriving your architecture rules from scratch on every single cycle. With skills, intent compounds. Your team’s architectural conventions, build steps, and historical “don’t do this because of that outage” notes are written once on the outside and read by the agent on every run.

Example skill excerpt:

```markdown
# CI Triage Skill
## Classification Rules
- env: Missing secrets or unprovisioned infrastructure. -> Escalate to human.
- flake: Test passes on a clean retry without code changes. -> File a report.
- bug: Deterministic failure tied directly to a recent commit. -> Draft a fix.

## Fix Patterns
- Auth tests -> Verify src/auth/middleware first.
- Database tests -> Check if recent migrations were applied in the CI env.

## Never Do
- Never disable a failing test to pass the build; always escalate.
- Never touch code inside src/payments/ or src/billing/.
```

### 08. Connectors: Letting the Loop Touch the Real World

A loop that can only see your local filesystem is severely limited. Connectors, built on the **Model Context Protocol (MCP)**, give your agent the ability to read your issue trackers, query live databases, hit staging APIs, and drop notifications into communication channels.

Connectors are the reason an agent moves from saying *“here is the fix”* to actively opening the PR, linking the tracking ticket, and alerting the team over Slack once the build turns green.

**High-value connectors to deploy first:**

- **GitHub/GitLab:** Reading repositories, branching, opening PRs, and reacting directly to webhook events.
- **Linear / Jira:** Automatically updating ticket states and linking PRs back to tracking items.
- **Slack / Discord:** Posting daily triage summaries and alerting humans when an escalation occurs.
- **Sentry / Error Trackers:** Investigating live error spikes and automatically drafting hotfixes for high-frequency alerts.

### 09. Sub-Agents: Isolating the Maker from the Checker

The most critical structural pattern in loop engineering is separating the agent that writes code from the agent that verifies it. As Addy Osmani points out, the model that wrote the code is always *“way too nice grading its own homework.”* This maps directly to the **Evaluator-Optimizer pattern** where one model generates the code, a completely separate sub-agent critiques it against the specification, and the cycle repeats.

Modern setups allow you to declare teams of subagents via local configuration files. You can configure your explorer to be a fast, cost-efficient model, while assigning your security and verification checker to a high-reasoning model running on maximum effort. Sub-agents burn more tokens since each one performs its own processing, but a verifier you actually trust is the only reason you can walk away.

---

## PART 3 · Build It Right or Don’t Build It

### 10. The State File: The Agent Forgets, the File Remembers

This is a component that sounds almost too simple to matter, yet it forms the structural backbone of every production loop. Whether it’s a Markdown file, a Linear board, or a JSON blob, you must maintain a persistent record of state outside of the active conversation window.

LLM sessions are stateless and naturally lose context over long durations. A loop without a persistent state file restarts its entire mental model from zero on every run; a loop with a state file seamlessly resumes where it left off.

Example state JSON:

```json
{
  "loop_id": "ci-triage",
  "last_run": "2026-06-15T03:30:00Z",
  "status": {
    "failures_classified": 7,
    "fixes_drafted": 3,
    "escalated_to_humans": 4
  },
  "in_progress": [
    {"branch": "claude/fix-auth-refresh", "status": "awaiting_ci"}
  ],
  "lessons_learned": [
    "PowerShell runner hits TLS issues on Windows; always fallback to bash.",
    "E2E checkouts require the stripe webhook secret; skip if missing."
  ]
}
```

**Where to house your state:**

- **In-repo Markdown (`STATE.md`):** Saved right at your project root or inside your configuration folder. Version-controlled, highly visible, and simple. Ideal for solo developers or small teams.
- **External systems (databases/Linear):** Survives cleanly across separate repositories and provides cross-team visibility for enterprise-scale loops.

### 11. The Minimum Viable Loop

If your target task successfully passed the initial 4-condition test, your goal is to build the absolute smallest functional loop possible. Avoid complex multi-agent swarms out of the gate. Stick to these four basic pillars:

1. **Scheduled automation** (heartbeat)
2. **Targeted skill** (project knowledge)
3. **State file** (continuity)
4. **Automated gate** (verification)

**Execution order rules:** Always make sure a manual run is 100% reliable first. Document that process into a single static skill. Wrap that skill into a functional loop execution. Only then schedule it as an automated background process. Skipping straight to scheduling is the number one reason loops fail in production.

> **The True North Metric**
>
> The only performance metric that matters is your **Cost per Accepted Change**. Do not optimize for tokens spent, tasks attempted, or total loops scheduled. If your human acceptance rate for the loop’s pull requests falls below 50%, you are stuck doing the manual review work the loop was supposed to save you from — meaning the loop is losing you money.

### 12. The “Ralph Wiggum” Loop: Avoiding Quiet Failures

Engineer Geoffrey Huntley documented this specific failure mode and named it after Ralph Wiggum (the cartoon character known for being oblivious to his own mistakes). In this scenario, an agent prematurely emits a completion token before the job is genuinely complete, causing the loop to exit on a half-done task while claiming everything is fine. Without objective, rigid gates, loops will routinely fail quietly while continuing to drain your budget.

**You are running a Ralph Wiggum loop if:**

- **You lack a real verifier:** You are simply asking a second agent to “review” code via conversation without running an external test suite. This is just two optimists blindly agreeing with each other.
- **Your completion metrics are soft:** “Done” is defined by the agent’s internal judgment rather than an objective compilation success, build, or passing test suite.
- **You lack hard caps:** The loop lacks a max token or runtime ceiling, running endlessly until a rate limit or a massive billing alert cuts it off.

**Critical failures to monitor:**

- **Goal drift:** In long-running agent sessions, each subsequent contextual summary step is lossy. Explicit boundaries and “do not touch” rules tend to completely vanish by turn 47. *Mitigation: Force the agent to re-read a base structural file like a standing high-level spec on every single iteration.*
- **Agentic laziness:** The loop decides a task is “good enough” at partial completion. *Mitigation: Implement a hard `/goal` parameter evaluated by a completely separate validation model.*

### 13. Comprehension Debt and Cognitive Surrender

This non-technical failure mode grows more dangerous as your automated loops get better, not worse. Addy Osmani highlights two major psychological risks:

- **Comprehension debt:** The faster your automated loops ship code, the wider the gap grows between what lives in your repository and what your engineering team actually understands. The bill that truly hurts isn’t your monthly API invoice; it’s the day your production system goes down and nobody on the team can read or debug the system required to fix it.
- **Cognitive surrender:** The subtle psychological urge to stop forming an independent technical opinion and blindly accept whatever code the loop outputs. Designing loops is an incredible multiplier when backed by human judgment, but it turns into a major liability when used to avoid thinking.

**How to mitigate comprehension debt:**

- **Force diff reviews:** If your team isn’t thoroughly reading the diffs of every single automated PR, you are renting comprehension debt at a devastating compound interest rate.
- **Audit your gates:** Periodically break your code on purpose to verify that your automated testing gates actually catch the errors you expect them to. Gates rot over time.
- **Restrict scope:** Lock your loops down to small, isolated, machine-checkable changes. Do not allow automated loops to touch high-level system architecture.

### 14. The Security Tax: Unattended Loops as Attack Surfaces

An unattended automation loop running with repository access is a live, unattended attack surface. Architect loops to explicitly defend against these vectors:

- **Unreviewed code promotion:** If a loop generates code faster than humans can review it, security vulnerabilities can easily slip through. Automation gates must include mandatory static analysis (SAST), dependency vulnerability scanning, and secret detection before code ever merges.
- **Skills as injection vectors:** A loop that pulls down unverified community skills inherits any malicious prompt injections hidden inside their descriptions. Always audit external skill sources before installing them.
- **Credential leaks in logs:** Debug logs on long-running looping agents can easily catch and output environmental variables, authentication tokens, or private keys. Disable verbose logging in production environments and actively sanitize what gets recorded.
- **Permission creep:** A loop that was originally granted read-only permissions often gets granted write access later on for basic convenience. Audit your loop’s API tokens and permissions scope every 30 days without fail.

---

## Summary Checklist: Avoid the Money Pits

- [ ] Did you run the 4-Condition Test? (Step 02)
- [ ] Is there an objective, automated gate (test/linter/build) instead of just an LLM "review"?
- [ ] Are your maker and checker tasks split across completely separate agents?
- [ ] Does the loop write its progress to a persistent state file?
- [ ] Have you configured a strict, unbypassable token budget cap?
- [ ] Is the loop blocked from touching subjective, architectural, or payment code?
- [ ] Are you actively reading every line of the diffs before hitting merge?

---

## Conclusion: The Leverage Moved. Your Job Did Too.

For the past two years, the ultimate leverage in working with coding agents lived directly at the prompt level. Success was determined by who wrote the best instructions, provided the cleanest context window, and generated the best one-shot output.

That phase is officially over. LLMs have become sophisticated enough that the true engineering leverage point has moved up a level: **into the design of the system that orchestrates them.** Your value as an engineer now lies in defining what they work on, when they trigger, how they log state, and what automated gates validate their success.

Build the loop. But build it like someone who intends to stay the engineer, not just the person who presses go.

---

## Mapping to this repository (orchestrator template)

| Article concept | Orchestrator artifact |
|-----------------|----------------------|
| Automations / cadence | `LOOP.md`, `patterns/`, host scripts (`loop-daily-triage-host.sh`, etc.) |
| Skills | `.grok/skills/*/SKILL.md`, synced to `.github/` / `.claude/` |
| Connectors (MCP) | `mcp-server/`, `.cursor/mcp.json`, `.grok/config.toml` |
| Sub-agents / verifier | `.grok/agents/loop-verifier.md`, `loop-verifier` skill (L1 report-only) |
| State file | `STATE.md`, `loop-run-log.md` |
| Token budget | `loop-budget.md`, `token_policy` in `project-manifest.yaml` |
| Cache-first loops | `/loop-triage`, `/loop-engineering` — manifest + lean cache mandatory |

See also: `reports/research/loops_research.md`, `LOOP.md`, `/loop-engineering` skill.