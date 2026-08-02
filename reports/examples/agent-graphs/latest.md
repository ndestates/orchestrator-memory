# Agent graph example — workstream diamond

Generated: `2026-07-25T07:51:57.302701+00:00` · HEAD `a555310`

## Topology

```mermaid
flowchart TD
  split["split: load registry + probes"]
  split --> vault_tip["vault:tip · OK"]
  vault_tip --> reduce["reduce: code barrier"]
  split --> ws_freemium_paypal["ws:freemium-paypal · OK"]
  ws_freemium_paypal --> reduce["reduce: code barrier"]
  split --> ws_multi_stream_graphs["ws:multi-stream-graphs · OK"]
  ws_multi_stream_graphs --> reduce["reduce: code barrier"]
  split --> ws_opensource_license["ws:opensource-license · OK"]
  ws_opensource_license --> reduce["reduce: code barrier"]
  split --> ws_product_graph["ws:product-graph · OK"]
  ws_product_graph --> reduce["reduce: code barrier"]
  split --> ws_webmcp_beta["ws:webmcp-beta · OK"]
  ws_webmcp_beta --> reduce["reduce: code barrier"]
  reduce --> synth["synthesize: mermaid + JSON"]
```

## Reduce (edge, free tokens)

```json
{
  "total_nodes": 6,
  "ok": 6,
  "failed": 0,
  "workstreams": 5,
  "by_status": {
    "held": 1,
    "active": 1,
    "held_ready": 1,
    "parked": 2
  },
  "failed_ids": []
}
```

## Nodes

| Node | Type | OK | Detail |
|------|------|----|--------|
| `vault:tip` | vault | True | ec3d8b02b6cdc650 |
| `ws:freemium-paypal` | workstream | True | held |
| `ws:multi-stream-graphs` | workstream | True | active |
| `ws:opensource-license` | workstream | True | held_ready |
| `ws:product-graph` | workstream | True | parked |
| `ws:webmcp-beta` | workstream | True | parked |

## How to re-run

```text
/multi-workstream list
/multi-workstream example
```

Diamond probes **workstream registry + vault tip only** — not product demos.
See plan: `docs/internal/MULTI-WORKSTREAM-SESSION-V2-PLAN.md`
