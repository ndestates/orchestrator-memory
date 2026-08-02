# Gemini Tool Calling / Function Calling for Orchestrator Tools

Gemini (via Google AI Studio or API) supports function calling for tools.

Use this to declare the orchestrator MCP tools as functions.

## Example Tool Declarations (for Gemini API or prompt)

```json
{
  "function_declarations": [
    {
      "name": "get_project_manifest",
      "description": "Load project manifest summary (stack, paths, token/chain/loop policy).",
      "parameters": {
        "type": "OBJECT",
        "properties": {}
      }
    },
    {
      "name": "read_cache_file",
      "description": "Read an allowlisted cache or registry file under PROJECT_ROOT (bounded).",
      "parameters": {
        "type": "OBJECT",
        "properties": {
          "relative_path": {
            "type": "STRING",
            "description": "Path relative to project root, e.g. docs/codebase/README.md"
          },
          "max_bytes": {
            "type": "INTEGER",
            "description": "Optional max bytes to read"
          }
        },
        "required": ["relative_path"]
      }
    },
    {
      "name": "get_latest_todo",
      "description": "Return latest TODO file path and open checklist items.",
      "parameters": {
        "type": "OBJECT",
        "properties": {
          "max_items": {
            "type": "INTEGER",
            "description": "Max open items to return (default 5)"
          }
        }
      }
    },
    {
      "name": "list_chains",
      "description": "List chains from chains/registry.yaml; optional intent keyword filter.",
      "parameters": {
        "type": "OBJECT",
        "properties": {
          "intent": {
            "type": "STRING",
            "description": "Optional keyword to filter chains by intent"
          }
        }
      }
    }
    // Add more from MCP tools: get_cache_freshness, get_loop_state, run_readonly_audit, etc.
  ]
}
```

## How to Use in Prompt

When using Gemini API:

```
You have access to these tools: [paste declarations above]

To use a tool, respond with function call in the specified format.

For example, to get manifest: call get_project_manifest
```

In Google AI Studio chat with tools enabled, define the functions.

For the orchestrator template, prefer MCP stdio/HTTP for clients that support it (Cursor with Gemini backend, etc.).

See mcp-server/README.md for deployment.

Adapt the full list of tools from mcp-server/src/orchestrator_mcp/server.py .
