# WebMCP imperative register (beta snippet)

Copy into app frontend only after operator confirms. APIs may change.

```js
/**
 * Progressive WebMCP registration.
 * Works when navigator.modelContext is missing (human UI only).
 */
const localRegistry = new Map();

const hasWebMCP =
  !!(globalThis.navigator &&
     navigator.modelContext &&
     typeof navigator.modelContext.registerTool === "function");

/**
 * @param {object} spec
 * @param {string} spec.name
 * @param {string} [spec.title]
 * @param {string} spec.description
 * @param {object} spec.inputSchema - JSON Schema object
 * @param {object} [spec.annotations] - e.g. { readOnlyHint: true }
 * @param {(input: object, client?: object) => Promise<unknown>|unknown} spec.execute
 */
export function registerTool(spec) {
  localRegistry.set(spec.name, spec);

  if (!hasWebMCP) return { registered: false, reason: "no_modelContext" };

  try {
    navigator.modelContext.registerTool({
      name: spec.name,
      title: spec.title || spec.name,
      description: spec.description,
      inputSchema: spec.inputSchema,
      annotations: spec.annotations || {},
      execute: async (input, client) => {
        // Never log secrets; keep errors agent-readable
        return await spec.execute(input, client);
      },
    });
    return { registered: true };
  } catch (err) {
    console.warn(`[webmcp] registerTool("${spec.name}") failed:`, err);
    return { registered: false, reason: String(err) };
  }
}

export function callLocal(name, input) {
  const tool = localRegistry.get(name);
  if (!tool) throw new Error(`Unknown tool: ${name}`);
  return tool.execute(input);
}

// Example (readonly)
registerTool({
  name: "getAvailability",
  title: "Get booking availability",
  description: "List bookable consultation times within a date range.",
  inputSchema: {
    type: "object",
    properties: {
      startDate: { type: "string", format: "date" },
      endDate: { type: "string", format: "date" },
    },
    required: ["startDate", "endDate"],
  },
  annotations: { readOnlyHint: true },
  execute: ({ startDate, endDate }) => {
    // App-specific: return slots; do not put secrets here
    return { startDate, endDate, slots: [] };
  },
});
```

See also: https://developer.chrome.com/docs/ai/webmcp/imperative-api  
