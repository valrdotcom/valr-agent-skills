# Subaccounts

> **Always call the API.** Do not answer from the examples in this file —
> call the endpoint via `valr_request.py` every time.

A VALR account can have multiple subaccounts, each with its own balances,
trading history, and margin/futures settings. The primary account has id `"0"`.

- Subaccount management requires a **primary account API key** with Trade or View permissions.
- To scope a request to a specific subaccount, see `references/authentication.md`.

## Contents

| Operation | Section | Endpoint |
|---|---|---|
| List all subaccounts | List Subaccounts | `GET /v1/account/subaccounts` |
| Get one subaccount by ID | Get Single Subaccount | `GET /v1/account/subaccount/{id}` |
| Create a new subaccount | Create Subaccount | `POST /v1/account/subaccount` |
| Rename a subaccount | Update Subaccount | `PUT /v1/account/subaccount` |
| Delete a subaccount | Delete Subaccount | `DELETE /v1/account/subaccount` |
| Move funds between accounts | Transfer Between Accounts | `POST /v1/account/subaccounts/transfer` |
| Get balances across all accounts | All Account Balances | `GET /v1/account/balances/all` |
| Cross-subaccount transfer history | Cross-Subaccount Transaction History | `GET /v1/account/transactionhistory/subaccounts` |
| Enable margin or futures | Enable Margin or Futures on a Subaccount | `PUT /v1/margin/account/status` |

> **Read the full section for any operation before calling the endpoint.**
> The table above is a routing aid — it does not show required fields,
> request body schemas, query parameters, or error codes.

## List Subaccounts

Returns all subaccounts including the primary account (id `"0"`).

```
GET /v1/account/subaccounts
```

**Authentication required.** Primary account key only.

### Usage

```bash
python3 scripts/valr_request.py GET /v1/account/subaccounts
```

### Response

Array of subaccount objects:

| Field | Type | Description |
|---|---|---|
| `id` | string | Subaccount public ID. `"0"` for the primary account |
| `label` | string | Human-readable name |

### Example Response

```json
[
  { "label": "Primary", "id": "0" },
  { "label": "Futures", "id": "1402613105484087296" },
  { "label": "Trading", "id": "902529770612256768" }
]
```

---

## Get Single Subaccount

Returns details for one subaccount. For proprietary subaccounts only `id` and
`label` are returned; KYC fields are omitted.

```
GET /v1/account/subaccount/{accountPublicId}
```

**Authentication required.** Primary account key only.

### Usage

```bash
python3 scripts/valr_request.py GET /v1/account/subaccount/1402613105484087296
```

### Example Response

```json
{
  "id": "1402613105484087296",
  "label": "Futures"
}
```

---

## Create Subaccount

Creates a new proprietary subaccount (label only, no KYC).
- Labels: alphanumeric, max 64 characters.
- Limit: 2000 subaccounts per account.

```
POST /v1/account/subaccount?isProprietarySubAccount=true
```

**Authentication required.** Primary account key with Trade permission.

### Usage

```bash
python3 scripts/valr_request.py POST \
  "/v1/account/subaccount?isProprietarySubAccount=true" \
  --body '{"label":"my-trading-desk"}'
```

### Request Body

| Field | Type | Required | Description |
|---|---|---|---|
| `label` | string | Yes | Alphanumeric label, max 64 characters |

### Response

```json
{ "id": "1481889851794235392" }
```

The returned `id` is the subaccount's public ID (string). Use it for all
subsequent operations targeting this subaccount.

### Error Codes

| Code | Meaning |
|---|---|
| `-11136` | Subaccount limit (2000) exceeded |
| `-11132` | Label already in use |

---

## Update Subaccount

Rename an existing proprietary subaccount.

```
PUT /v1/account/subaccount?isProprietarySubAccount=true
```

**Authentication required.** Primary account key with Trade permission.

### Usage

```bash
python3 scripts/valr_request.py PUT \
  "/v1/account/subaccount?isProprietarySubAccount=true" \
  --body '{"id":1481889851794235392,"label":"renamed-desk"}'
```

### Request Body

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | integer | Yes | Subaccount ID as an integer (same value as the string id, cast to int) |
| `label` | string | Yes | New label |

**Note:** The `id` field in the request body is an integer, even though
`GET /v1/account/subaccounts` returns id as a string. Cast the string to an
integer when constructing the request.

### Response

Empty body. `202 Accepted`.

---

## Delete Subaccount

Deletes a subaccount. Requirements:
- Zero balances
- No active margin
- Futures must not be enabled

```
DELETE /v1/account/subaccount
```

**Authentication required.** Primary account key with Trade permission.

### Usage

```bash
python3 scripts/valr_request.py DELETE /v1/account/subaccount \
  --body '{"id":1481889851794235392}'
```

### Request Body

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | integer | Yes | Subaccount ID as an integer |

### Response

Empty body. `204 No Content`.

### Error Codes

| Code | Meaning |
|---|---|
| `-11163` | Cannot delete — subaccount has non-zero balances |
| `-19225` | Cannot delete — margin is enabled on this subaccount |
| `-19228` | Cannot delete — futures is enabled on this subaccount |

**Note:** Subaccounts with margin or futures enabled cannot be deleted. Transfer
all balances out first (see Transfer below).

---

## Transfer Between Accounts

Transfer funds between any two accounts (primary or subaccounts). The source
account must have sufficient available balance.

```
POST /v1/account/subaccounts/transfer
```

**Authentication required.** Primary account key with Internal Transfer
permission. A subaccount key can only transfer out of the subaccount it belongs
to.

### Usage

```bash
# Transfer from primary (id 0) to a subaccount
python3 scripts/valr_request.py POST /v1/account/subaccounts/transfer \
  --body '{"fromId":0,"toId":1402613105484087296,"currencyCode":"USDT","amount":"100","allowBorrow":false}'

# Transfer from a subaccount back to primary
python3 scripts/valr_request.py POST /v1/account/subaccounts/transfer \
  --body '{"fromId":1402613105484087296,"toId":0,"currencyCode":"USDT","amount":"100","allowBorrow":false}'
```

### Request Body

| Field | Type | Required | Description |
|---|---|---|---|
| `fromId` | integer | Yes | Source account ID. `0` for the primary account |
| `toId` | integer | Yes | Destination account ID. `0` for the primary account |
| `currencyCode` | string | Yes | Currency to transfer (e.g. `"USDT"`, `"BTC"`) |
| `amount` | string | Yes | Amount to transfer |
| `allowBorrow` | boolean | Yes | If `true`, borrow against collateral if balance is insufficient. Only works on margin-enabled subaccounts. Use `false` unless you specifically want to borrow |

### Response

```json
{ "id": "641767" }
```

The response contains the transfer's transaction ID.

### Notes

- Transfers settle synchronously. Confirm via
  `GET /v1/account/balances --subaccount-id {id}` if needed.
- Primary account ID is `0` (integer) in the request body.
- `allowBorrow: false` is the safe default. Set `true` only for
  margin-enabled subaccounts when you intentionally want to borrow.

### Error Codes

| Code | Meaning |
|---|---|
| `-11133` | Internal transfer not permitted for this key |

---

## All Account Balances

Returns non-zero balances grouped by account across primary and all subaccounts.
Accounts with no balances are omitted.

```
GET /v1/account/balances/all
```

**Authentication required.** Primary account key only.

### Usage

```bash
python3 scripts/valr_request.py GET /v1/account/balances/all
```

### Response

Array of account balance groups:

| Field | Type | Description |
|---|---|---|
| `account.id` | string | Account public ID (`"0"` for primary) |
| `account.label` | string | Account label |
| `balances` | array | Non-zero balance objects for this account |
| `balances[].currency` | string | Currency code |
| `balances[].available` | string | Amount available to trade or withdraw |
| `balances[].reserved` | string | Amount locked in open orders |
| `balances[].total` | string | Total (`available` + `reserved`) |
| `balances[].updatedAt` | string | ISO 8601 timestamp of last update |
| `balances[].lendReserved` | string | Reserved for active lending offers |
| `balances[].borrowReserved` | string | Collateral reserved against borrowed funds |
| `balances[].borrowedAmount` | string | Total outstanding borrows |

### Example Response

```json
[
  {
    "account": { "label": "Futures", "id": "1402613105484087296" },
    "balances": [
      {
        "currency": "USDT",
        "available": "4.94063025",
        "reserved": "0",
        "total": "8.93943025",
        "updatedAt": "2026-03-13T04:00:00.025Z",
        "lendReserved": "0",
        "borrowReserved": "3.9988",
        "borrowedAmount": "0"
      }
    ]
  },
  {
    "account": { "label": "Primary", "id": "0" },
    "balances": [
      {
        "currency": "USDT",
        "available": "9668103.08",
        "reserved": "141128.24",
        "total": "9809231.32",
        "updatedAt": "2026-03-11T14:43:42.428Z",
        "lendReserved": "0",
        "borrowReserved": "0",
        "borrowedAmount": "0"
      }
    ]
  }
]
```

---

## Cross-Subaccount Transaction History

Returns transaction history across all subaccounts. Only subaccounts with
activity in the requested time window appear.

```
GET /v1/account/transactionhistory/subaccounts
```

**Authentication required.** Primary account key only.

### Query Parameters

| Parameter | Type | Description |
|---|---|---|
| `skip` | integer | Pagination offset (default 0) |
| `limit` | integer | Max results per subaccount (default and max 100) |
| `transactionTypes` | string | Comma-separated transaction type filter |
| `currency` | string | Filter by currency code (e.g. `USDT`) |
| `startTime` | string | ISO 8601 start of window (default: 1 day ago) |
| `endTime` | string | ISO 8601 end of window (max 7 days after startTime) |

### Usage

```bash
# Last 24 hours (default)
python3 scripts/valr_request.py GET \
  "/v1/account/transactionhistory/subaccounts?limit=50"

# Specific time range
python3 scripts/valr_request.py GET \
  "/v1/account/transactionhistory/subaccounts?startTime=2026-03-01T00:00:00Z&endTime=2026-03-07T00:00:00Z"
```

### Response

Array of per-subaccount groups. Subaccounts with no activity in the window are
omitted:

| Field | Type | Description |
|---|---|---|
| `id` | string | Subaccount public ID |
| `label` | string | Subaccount label |
| `transactions` | array | Transactions for this subaccount in the window |
| `transactions[].id` | string | Transaction UUID |
| `transactions[].transactionType.type` | string | Type code (e.g. `INTERNAL_TRANSFER`, `FUTURES_PNL_PROFIT`) |
| `transactions[].transactionType.description` | string | Human-readable type |
| `transactions[].debitCurrency` | string | Currency debited (present if debit occurred) |
| `transactions[].debitValue` | string | Amount debited |
| `transactions[].creditCurrency` | string | Currency credited (present if credit occurred) |
| `transactions[].creditValue` | string | Amount credited |
| `transactions[].feeCurrency` | string | Fee currency (if applicable) |
| `transactions[].feeValue` | string | Fee amount (if applicable) |
| `transactions[].eventAt` | string | ISO 8601 timestamp |

### Notes

- Time window cannot exceed 7 days. Use multiple calls with non-overlapping
  windows for longer ranges.
- Subaccounts absent from the response have no transactions in the window —
  they may still have history outside it.

---

## Enable Margin or Futures on a Subaccount

Enables margin or perpetual futures trading on a subaccount. Must be scoped to
the target subaccount (not the primary account).

```
PUT /v1/margin/account/status
```

**Authentication required.** Must be scoped to the target subaccount: either
use a subaccount API key, or pass `--subaccount-id` with a primary account key.

**This operation is irreversible.** Futures and margin cannot be disabled once
enabled. Subaccounts with either enabled cannot be deleted.

> **CRITICAL:** Always warn the user that enabling futures/margin is permanent
> and irreversible. Always call PUT even if status appears already enabled
> (it's idempotent). Report the result to the user including the permanence note.

### Usage

```bash
# Enable futures on a subaccount (using primary key + subaccount-id)
python3 scripts/valr_request.py PUT /v1/margin/account/status \
  --subaccount-id 1402613105484087296 \
  --body '{"accountStatusFieldName":"FUTURES_ENABLED","enabled":true}'

# Enable margin on a subaccount
python3 scripts/valr_request.py PUT /v1/margin/account/status \
  --subaccount-id 1402613105484087296 \
  --body '{"accountStatusFieldName":"MARGIN_ENABLED","enabled":true}'
```

### Request Body

| Field | Type | Required | Description |
|---|---|---|---|
| `accountStatusFieldName` | string | Yes | `"FUTURES_ENABLED"` or `"MARGIN_ENABLED"` |
| `enabled` | boolean | Yes | Must be `true`. Setting `false` returns an error |

### Response

Empty body. `200 OK`. Enabling an already-enabled subaccount is idempotent —
it returns `200` with no error.

### Error Codes

| Code | Meaning |
|---|---|
| `-21100` | Request was made against the primary account. Must target a subaccount |
| `-19228` | Attempted to disable futures — not supported |
| `-19225` | Attempted to disable margin — not supported |
| `-11420` | Proof of address required before enabling futures on this subaccount |

**Note on account verification:** If the API call fails with `-11420`, the
user's main account must be fully verified before futures can be enabled on any
subaccount. Direct them to upgrade verification in their VALR account settings.

### Workflow: Finding and Enabling a Futures Subaccount

To find which subaccounts have futures enabled without knowing IDs in advance:

```bash
# 1. List all subaccounts
python3 scripts/valr_request.py GET /v1/account/subaccounts

# 2. Check each subaccount's status
python3 scripts/valr_request.py GET /v1/margin/account/status \
  --subaccount-id <id>
# Look for: "futuresEnabled": true

# 3. If none found and you want to enable a new one, create a subaccount first
python3 scripts/valr_request.py POST \
  "/v1/account/subaccount?isProprietarySubAccount=true" \
  --body '{"label":"futures-trading"}'

# 4. Enable futures on it (irreversible)
python3 scripts/valr_request.py PUT /v1/margin/account/status \
  --subaccount-id <new-id> \
  --body '{"accountStatusFieldName":"FUTURES_ENABLED","enabled":true}'
```
