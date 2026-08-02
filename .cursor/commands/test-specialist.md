# /test-specialist

> Write/improve/convert tests (Pest preferred) for project. Preserves logic; follows safety. Use on /test-specialist-agent or test tasks.

**Platform:** Cursor · same skill as Grok `/test-specialist` · Claude `/test-specialist`

Execute this skill for the current project. Cache-first. Manifest-first.

Argument hint: `What to test or improve, e.g. 'valuation service', 'convert legacy Property test`

# Test Specialist Agent

1. Run `/load-project-cache-first` (TESTING.md etc).
2. Read and embody the full instructions in [`.grok/agents/test-specialist-agent.md`](../../.grok/agents/test-specialist-agent.md).
3. DDEV + test DB only.
4. Security checklist if form/dep changes from tests.
5. Keep behavior identical on conversions.
6. Call out infra/logic impacts.

Run tests to green; cite cache.

User focus (optional): use any extra chat text as $ARGUMENTS.
