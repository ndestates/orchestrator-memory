# Loqate Address Capture API — Canonical Reference (ground truth)

```yaml
vendor: loqate
service: address-capture
last_verified: 2026-06-19
sources:
  - https://docs.loqate.com/llms.txt
  - https://docs.loqate.com/api-reference/address-capture/quickstart
  - https://docs.loqate.com/api-reference/address-capture/find
  - https://docs.loqate.com/api-reference/address-capture/retrieve
```

**Anti-hallucination:** Use only endpoints and parameters listed here. HTTPS only (no HTTP). If a field is not documented, fetch `sources` — never invent query params or response keys.

## Flow (always two-step)

1. **Find** — type-ahead search; returns `Items[]` with `Type` = `Address` or `Container`.
2. **Retrieve** — full formatted address using `Id` from Find.

If Find returns `Type: Container`, run a second Find with `Container={id}` (omit `Text`) before Retrieve.

## Endpoints (HTTPS only)

| Step | URL |
|------|-----|
| Find | `https://api.addressy.com/Capture/Interactive/Find/v1.10/json6.ws` |
| Retrieve | `https://api.addressy.com/Capture/Interactive/Retrieve/v1.20/json6.ws` |

Alternate response formats in docs use `json3.ws` — pin one format per app; do not mix.

## Auth

Query param `Key=$LOQATE_API_KEY` on every request. Create key at [account.loqate.com](https://account.loqate.com/) → Add a service → Address Capture.

## Find — parameters (allowlist)

| Param | Required | Notes |
|-------|----------|-------|
| `Key` | yes | API key |
| `Text` | yes* | Search text (*omit when using Container) |
| `Container` | no | Container id from prior Find |
| `Countries` | no | ISO2 filter e.g. `GB,US` |
| `Limit` | no | Max results |
| `Language` | no | Preferred language |

## Find — response shape

```json
{
  "Items": [
    {
      "Id": "GB|RM|A|4624695|A1|ENG",
      "Type": "Address",
      "Text": "Loqate Ltd The Foundation Herons Way",
      "Highlight": "0-6",
      "Description": "Chester Business Park Chester CH4 9GB"
    }
  ]
}
```

`Type` values: `Address`, `Container`. **Ids are temporary** — do not persist Find ids long-term; Retrieve promptly after user selection.

## Retrieve — parameters

| Param | Required |
|-------|----------|
| `Key` | yes |
| `Id` | yes | From Find `Items[].Id` |

## Retrieve — key fields (store in app DB)

`Line1`–`Line5`, `City`, `Province`, `PostalCode`, `CountryIso2`, `CountryName`, `Company`, `BuildingName`, `BuildingNumber`, `Street`, `Label`, `DataLevel`, `Type`.

Multiple `Items` possible (e.g. ENG + CYM) — pick `Language` matching UI locale.

## Example requests

```bash
# Find
curl -G "https://api.addressy.com/Capture/Interactive/Find/v1.10/json6.ws" \
  --data-urlencode "Key=$LOQATE_API_KEY" \
  --data-urlencode "Text=Herons Way Chester" \
  --data-urlencode "Countries=GB"

# Retrieve (after user picks Id)
curl -G "https://api.addressy.com/Capture/Interactive/Retrieve/v1.20/json6.ws" \
  --data-urlencode "Key=$LOQATE_API_KEY" \
  --data-urlencode "Id=GB|RM|A|4624695|A1|ENG"
```

## Laravel integration pattern

- **Backend proxy** (recommended): Livewire/Alpine calls your `/api/address/find` and `/api/address/retrieve` — never expose `LOQATE_API_KEY` to browser.
- **Rate limit** proxy routes; log usage; cache nothing containing raw PII beyond business need.
- Store normalized address columns on Signer/Customer models after Retrieve.

## Env vars (allowlist)

`LOQATE_API_KEY`, `LOQATE_DEFAULT_COUNTRIES` (optional, e.g. `GB`).

## Verification gate

After wiring: Find returns ≥1 Item for known test string; Retrieve returns `PostalCode` + `CountryIso2` for selected Id.