# Integrate Loqate Address Capture into my application

You are integrating Loqate (GBG) Address Capture for type-ahead find + structured retrieve. **Ground truth:** `.grok/skills/loqate-address-integration/references/loqate-api-canonical.md` — never invent endpoints or params.

## My application context

<my_stack>
Stack: [from manifest — e.g. Laravel 12 + Livewire + Filament 5]
App: [ndestates-io | e-ndsign | other]
Surface: [signer form | checkout billing address | Filament admin | other]
Countries: [GB | GB,US | ...]
</my_stack>

## Step 1 — API key

Create Address Capture key at account.loqate.com. Set `LOQATE_API_KEY` in DDEV `.env` / DO secrets.

## Step 2 — Backend proxy (required)

Never expose key client-side. Add authenticated or rate-limited routes:

- `GET /api/address/find?text=...&countries=...`
- `GET /api/address/retrieve?id=...`

Proxy to `api.addressy.com` Find v1.10 + Retrieve v1.20 (HTTPS only).

## Step 3 — Frontend type-ahead

Debounce Find as user types; on `Type: Container` run second Find with `Container`; on `Type: Address` run Retrieve; populate form fields from Retrieve `Items[0]` (match `Language`).

## Step 4 — Persist normalized address

Map `Line1`, `City`, `PostalCode`, `CountryIso2`, etc. to model columns. Do not store temporary Find ids.

## Step 5 — Filament / Livewire

Wire Loqate component on Signer create, customer checkout, or proof-of-address fields. Cite laravel-expert-agent patterns.

## Verify before done

Find + Retrieve succeed for test query; proxy rate-limited; key not in frontend bundle; guardian + `/eval-maintenance-task --task=loqate-address`.