#!/usr/bin/env python3
"""
Anthropic Prompt Caching Examples for the Orchestrator Project

Demonstrates:
- System prompt caching
- Tool definition caching
- Long document / large context caching
- Combined usage

This is for direct `anthropic` SDK usage (scripts, custom agents, MCP tools, evals).

Run: pip install anthropic
Set ANTHROPIC_API_KEY

See also:
- reports/research/claude_usage_guide.md (expanded section)
- reports/research/xai-prompt-caching.md (for Grok comparison)
"""

import anthropic
import os

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def print_usage(usage):
    print("Usage:", usage.model_dump_json(indent=2))


# ------------------------------------------------------------------
# 1. Basic System Prompt Caching
# ------------------------------------------------------------------
def example_system_cache():
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": "You are an expert literary analyst. Always ground your analysis in specific quotes from the text.",
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {"role": "user", "content": "What are the main themes in Pride and Prejudice?"}
        ],
    )
    print("=== System Cache Example ===")
    print(response.content[0].text[:300] + "...")
    print_usage(response.usage)


# ------------------------------------------------------------------
# Crucial note: Will our caching requests be respected?
# ------------------------------------------------------------------
# YES — when using the official Anthropic SDK directly with correct
# placement of `cache_control={"type": "ephemeral"}`, Anthropic's backend
# respects the directive and caches the prefix.
#
# Confirm success by looking at the usage dict:
#   - cache_creation_input_tokens on first call
#   - cache_read_input_tokens (and lower billed input_tokens) on hits
#
# Requirements:
# - Direct SDK calls only (not consumer claude.ai)
# - Exact prefix match on follow-up requests
# - Official client (many wrappers drop the field)
# - Supported model + sufficient prefix size
#
# Full details + caveats in reports/research/claude_usage_guide.md
# ------------------------------------------------------------------


# ------------------------------------------------------------------
# 2. Tool Definition Caching
# ------------------------------------------------------------------
def example_tool_cache():
    tools = [
        {
            "name": "get_project_info",
            "description": "Return high-level information about the current orchestrator project.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "aspect": {
                        "type": "string",
                        "enum": ["manifest", "skills", "chains", "loops", "deploy"],
                    }
                },
                "required": ["aspect"],
            },
            "cache_control": {"type": "ephemeral"},
        },
        {
            "name": "search_codebase",
            "description": "Search files and content in the orchestrator repository.",
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            "cache_control": {"type": "ephemeral"},
        },
    ]

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system="You are a helpful orchestrator assistant with access to tools.",
        messages=[
            {"role": "user", "content": "What skills are available for multi-AI work?"}
        ],
        tools=tools,
    )
    print("\n=== Tool Cache Example ===")
    print(response.content[0].text[:300] + "...")
    print_usage(response.usage)


# ------------------------------------------------------------------
# 3. Long Document Caching (e.g. large spec or codebase summary)
# ------------------------------------------------------------------
def example_long_document_cache():
    # Simulate loading a large document (in real use: read from file)
    long_context = """
    # Orchestrator Project Overview (simulated large document)

    The orchestrator is a manifest-first, cache-first template for AI-assisted development.
    It supports Grok, Claude, Copilot, and Gemini through parallel directory structures.

    Key components:
    - Manifests (.grok/project-manifest.yaml, .claude/, .github/, .gemini/)
    - Skills and agents in .grok/skills/
    - Chains in chains/registry.yaml
    - Lean cache in docs/codebase/
    - Sync script: scripts/sync_grok_to_github_claude.py
    - Non-destructive deploys to wave apps
    - Jersey DP/AML compliance experts (jersey-data-protection-expert, jersey-aml-compliance-expert)
    - Multi-AI best practices and prompt caching guidance
    """ * 5  # Simulate a long document by repeating

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": "You are an expert on the orchestrator template. Use the provided project context.",
                "cache_control": {"type": "ephemeral"},
            },
            {
                "type": "text",
                "text": long_context,
                "cache_control": {"type": "ephemeral"},
            },
        ],
        messages=[
            {
                "role": "user",
                "content": "Explain how prompt caching should be used when writing custom agents for this project.",
            }
        ],
    )
    print("\n=== Long Document Cache Example ===")
    print(response.content[0].text[:400] + "...")
    print_usage(response.usage)


# ------------------------------------------------------------------
# 4. Combined Example (System + Tools + Long Document)
# ------------------------------------------------------------------
def example_combined():
    long_doc = "Large stable project documentation here..." * 20  # placeholder

    tools = [
        {
            "name": "read_file",
            "description": "Read content from a project file.",
            "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}},
            "cache_control": {"type": "ephemeral"},
        }
    ]

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": "You are a senior architect for the orchestrator project.",
                "cache_control": {"type": "ephemeral"},
            },
            {
                "type": "text",
                "text": long_doc,
                "cache_control": {"type": "ephemeral"},
            },
        ],
        messages=[{"role": "user", "content": "Review this approach for tool caching."}],
        tools=tools,
    )
    print("\n=== Combined Cache Example ===")
    print(response.content[0].text[:300] + "...")
    print_usage(response.usage)


if __name__ == "__main__":
    example_system_cache()
    example_tool_cache()
    example_long_document_cache()
    example_combined()

    print("\nTip: On subsequent calls with identical cached prefixes, watch for high 'cache_read_input_tokens' and lower billed input_tokens.")