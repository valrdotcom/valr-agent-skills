# Account

> **Always call the API.** Do not answer from the examples in this file —
> call the endpoint via `{baseDir}/scripts/valr_request.py` every time.

This file covers:

- **Account balances** — `GET /v1/account/balances` — retrieve holdings for all currencies, including margin-affected and negative balances
- **API key info** — `GET /v1/account/api-keys/current` — check permissions and scope of the current key

## Get Account Balances

Retrieve balances for all currencies held in the account.

```
GET /v1/account/balances
```

**Authentication required.** Needs View permission.

### Usage

```bash
# All balances (may include zero-balance entries)
python3 {baseDir}/scripts/valr_request.py GET /v1/account/balances

# Recommended: pass excludeZeroBalances=true to reduce noise server-side
python3 {baseDir}/scripts/valr_request.py GET "/v1/account/balances?excludeZeroBalances=true"

# For a specific subaccount (requires the numeric subaccount ID)
# If you only know the name (e.g. "Futures"), resolve it first: GET /v1/account/subaccounts
python3 {baseDir}/scripts/valr_request.py GET "/v1/account/balances?excludeZeroBalances=true" --subaccount-id 12345
```

### Query parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `excludeZeroBalances` | boolean | `false` | When `true`, omits most zero-balance currencies from the response. Significantly reduces payload size. A small number of previously-active zero-balance currencies may still appear — filter client-side on `total != "0"` to remove them (use `!=` not `>` to preserve negative balances on margin accounts). |

### Response

Returns an array of balance objects. The response may include zero-balance
currencies — see `excludeZeroBalances` above to reduce them server-side.

| Field | Type | Description |
|---|---|---|
| `currency` | string | Currency code, e.g. `"BTC"`, `"USDT"` |
| `available` | string | Amount available to trade or withdraw |
| `reserved` | string | Amount locked in open orders and not available to trade or withdraw until those orders are filled or cancelled |
| `total` | string | Total balance. Equals `available + reserved` when no borrowing or lending is active. Can be negative on margin-enabled accounts with outstanding borrows (see [Margin-Affected Balances](#margin-affected-balances) below). |
| `updatedAt` | string | ISO 8601 timestamp of last update |
| `lendReserved` | string | Amount reserved for active lending offers |
| `borrowReserved` | string | Collateral reserved against borrowed funds |
| `borrowedAmount` | string | Total borrowed (loans outstanding) |

All numeric values are returned as strings to preserve decimal precision.

### Example Response

```json
[
  {
    "currency": "BTC",
    "available": "0.12500000",
    "reserved": "0.01000000",
    "total": "0.13500000",
    "updatedAt": "2024-01-15T10:30:00.000Z",
    "lendReserved": "0",
    "borrowReserved": "0",
    "borrowedAmount": "0"
  },
  {
    "currency": "USDT",
    "available": "500.00",
    "reserved": "100.00",
    "total": "600.00",
    "updatedAt": "2024-01-15T10:29:55.000Z",
    "lendReserved": "0",
    "borrowReserved": "0",
    "borrowedAmount": "0"
  }
]
```

### Presenting balances to a user

> **Tip:** Use `?excludeZeroBalances=true` to reduce noise — it cuts the
> response from hundreds of currencies down to just those with activity. A
> small number of previously-active zero-balance currencies may still appear;
> filter on `total != "0"` client-side to remove them. Do not filter on
> `total > "0"` — this would hide negative balances on margin-enabled accounts
> (see [Margin-Affected Balances](#margin-affected-balances) below).
>
> **REQUIRED: Always distinguish `available` from `total` when presenting
> balances.** Do not skip this step.
>
> - `available` = the amount free to trade or withdraw right now. **This is the
>   number to show when a user asks "what's available to trade?"**
> - `reserved` = locked in open orders; cannot be used until those orders fill
>   or are cancelled.
> - `total` = `available` + `reserved`.
>
> **Never report `total` as if it is all freely available.** Always show
> `available` as the tradeable amount. If `reserved` is non-zero for any
> currency, explicitly call this out — e.g. "X USDT is locked in open orders
> and not available to trade." Silently omitting a non-zero `reserved` value is
> incorrect.

### Margin-Affected Balances

On margin-enabled subaccounts, the full balance formula is:

```
total = available + reserved + borrowReserved + lendReserved - borrowedAmount
```

When no borrowing or lending is active this simplifies to `total = available + reserved`.

**Negative `total`:** A currency with `borrowedAmount` exceeding holdings has a
negative `total` — the user owes that amount. For example, `total: "-30.5695"`
with `borrowedAmount: "30.5695"` and `available: "0"` means the user has
borrowed 30.57 USDT and holds none.

**`borrowReserved`:** Collateral locked from a different currency to secure a
borrow. It reduces `available` on the collateral currency but remains part of
`total` — e.g. `available: "9419.75"`, `borrowReserved: "580.26"`,
`total: "10000.01"`.

**Presentation guidance:**

- A negative `total` is a debt — present it as an amount owed, not a zero balance.
- A zero or negative `available` does not mean orders cannot be placed. On
  margin-enabled accounts, orders and withdrawals can still borrow against
  collateral when `allowBorrow` is enabled.
- When `borrowedAmount` is non-zero, note that interest accrues hourly.
- When `borrowReserved` is non-zero, explain it is collateral securing a borrow
  in another currency.

### Notes

- A `202 Accepted` status is not used for this endpoint — the response is always
  the current balance data directly.
- Subaccount impersonation: include `--subaccount-id` to query a subaccount's
  balances using the primary account API key.
- To retrieve balances across all accounts at once, use
  `GET /v1/account/balances/all` — see `{baseDir}/references/subaccounts.md`.

## API Key Info

Retrieve the permissions and metadata for the API key used to make the request.

```
GET /v1/account/api-keys/current
```

**Authentication required.** Needs View permission.

### Usage

```bash
python3 {baseDir}/scripts/valr_request.py GET /v1/account/api-keys/current
```

### Response

| Field | Type | Description |
|---|---|---|
| `label` | string | Human-readable name assigned to the key |
| `permissions` | string[] | Scopes granted to this key (see below) |
| `addedAt` | string | ISO 8601 timestamp of when the key was created |
| `isSubAccount` | boolean | Whether this key belongs to a subaccount |
| `allowedIpAddressCidr` | string | IP whitelist in CIDR notation (omitted if unrestricted) |
| `allowedWithdrawAddressList` | array | Withdrawal address whitelist (omitted if unrestricted) |

**Permission values:**

| Value | What it allows |
|---|---|
| `"View access"` | Read balances, orders, trade history, and market data |
| `"Trade"` | Place and cancel orders |
| `"Withdraw"` | Withdraw crypto and fiat |
| `"Internal Transfer"` | Transfer funds between subaccounts (see `{baseDir}/references/subaccounts.md`) |
| `"Link bank account"` | Link and manage bank accounts |

### Notes

- If `allowedIpAddressCidr` is absent from the response, the key has **no IP
  restriction** — it can be used from any IP address. Mention this to the user.
- If `allowedWithdrawAddressList` is absent, the key has **no withdrawal address
  restriction**. Mention this to the user.

### Example Response

```json
{
  "label": "trading-bot",
  "permissions": [
    "View access",
    "Trade"
  ],
  "addedAt": "2024-06-13T09:00:00.000Z",
  "isSubAccount": false
}
```

In this example, both `allowedIpAddressCidr` and `allowedWithdrawAddressList`
are absent — the key is unrestricted in both respects.
