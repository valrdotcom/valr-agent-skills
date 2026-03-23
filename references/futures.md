# Perpetual Futures

> **Always call the API.** Do not answer from the examples in this file —
> call the endpoint via `valr_request.py` every time.

VALR perpetual futures are cryptocurrency derivatives that track the underlying
asset with no expiry. They involve **positions** (long/short), **leverage**,
hourly **funding payments**, and the risk of **liquidation**.

Read the relevant section for the task at hand.

## Contents

| What you need | Section | Key endpoint |
|---|---|---|
| Subaccount setup and enablement | Account Requirements | *(see also `references/subaccounts.md`)* |
| Available leverage tiers for a pair | Leverage Tiers | `GET /v1/public/risklimit/{currencyPair}` |
| Available futures pairs and funding rates | Futures Market Data | `GET /v1/public/futures/info` |
| Past funding rates for a pair (public) | Futures Market Data | `GET /v1/public/futures/funding/history` |
| View or change leverage for a pair | Leverage Configuration | `GET /v1/margin/leverage/{currencyPair}` |
| View open positions | Open Positions | `GET /v1/positions/open` |
| View closed positions (detail or summary) | Closed Positions | `GET /v1/positions/closed` |
| Position lifecycle events | Position History | `GET /v1/positions/history` |
| Funding payments I received/paid on my positions | Account Funding History | `GET /v1/positions/funding/history` |

## Account Requirements

### Futures requires a subaccount

- Perpetual futures **cannot be traded on a VALR primary account** — only on subaccounts with futures explicitly enabled.
- Futures enablement is one-time and irreversible. The subaccount cannot be deleted while futures is enabled.
- Enable via `PUT /v1/margin/account/status`. See `references/subaccounts.md` for the full workflow.

All futures API calls must be scoped to a futures-enabled subaccount. How you
do this depends on your API key type (see `references/authentication.md`):

- **Main account key**: pass `--subaccount-id YOUR_SUBACCOUNT_ID` on every
  futures call. `valr_request.py` sets the `X-VALR-SUB-ACCOUNT-ID` header and
  includes the ID in the request signature automatically. See
  `references/subaccounts.md` to discover the subaccount ID.
- **Subaccount key issued on a futures-enabled subaccount**: no extra flag
  needed — the key is already scoped to that subaccount.

### Checking whether futures is enabled

Use `GET /v1/margin/account/status` scoped to the relevant subaccount. See
`references/margin.md` for field descriptions and the error returned when
futures is not enabled.

**Note (main account keys):** Calling `GET /v1/positions/open` without
`--subaccount-id` silently returns `[]` rather than an error, even if futures
positions exist on a subaccount. Always scope futures calls to the correct
subaccount.

## Leverage Tiers (Public)

### Available tiers — `GET /v1/public/risklimit/{currencyPair}`

Returns all available leverage tiers for a perpetual futures pair. No
authentication required.

```bash
python3 scripts/valr_request.py GET /v1/public/risklimit/BTCUSDTPERP
```

Response is an array of objects, one per tier, ordered ascending by
`leverageMultiple`:

| Field | Type | Description |
|---|---|---|
| `pairSymbol` | string | Pair the tiers apply to, e.g. `BTCUSDTPERP` |
| `leverageMultiple` | number | Leverage multiplier for this tier, e.g. `10` |
| `initialMarginFraction` | number | Fraction of position value required as initial collateral to open a position at this leverage |
| `maintenanceMarginFraction` | number | Minimum fraction required to keep the position open; falling below triggers liquidation |
| `autoCloseMarginFraction` | number | Fraction at which VALR begins closing the position |
| `riskLimitValue` | number | Maximum position size (in `riskLimitCurrency`) permitted at this leverage tier |
| `riskLimitCurrency` | string | Currency of `riskLimitValue`, e.g. `USDT` |
| `isDefault` | boolean | `true` for the tier applied automatically when leverage has not been explicitly set |

**All numeric fields are JSON `number` type** — unlike most VALR API
responses where numeric values are returned as strings.

**Key observations from live data:**
Tiers range from 1x to 60x (default 10x). Higher leverage reduces
maximum position size (`riskLimitValue`).

**Non-futures pairs** (e.g. spot pairs like `BTCUSDT`) return an empty
array `[]` rather than an error.

The `leverageMultiple` values from this endpoint are the only valid inputs
when setting leverage via `PUT /v1/margin/leverage/{currencyPair}` (see
"Leverage Configuration" section below).

## Futures Market Data (Public)

These endpoints require no authentication.

### Available pairs — `GET /v1/public/futures/info`

Returns an array of all active perpetual futures pairs with current funding
and open interest data.

```bash
python3 scripts/valr_request.py GET /v1/public/futures/info
```

Response is an array, one object per pair:

| Field | Type | Description |
|---|---|---|
| `currencyPair` | string | Pair symbol, e.g. `BTCUSDTPERP` |
| `estimatedFundingRate` | string (decimal) | Current estimated funding rate for the next settlement. Positive = longs pay shorts; negative = shorts pay longs |
| `openInterest` | string (decimal) | Total open contracts in the base currency |
| `nextFundingRun` | number | Unix epoch milliseconds — next scheduled funding settlement |
| `nextPnlRun` | number | Unix epoch milliseconds — next PnL settlement (typically same as `nextFundingRun`) |

**Pair naming:** All VALR perpetual futures pairs use `{BASE}USDTPERP`
(e.g. `BTCUSDTPERP`, `ETHUSDTPERP`, `SOLUSDTPERP`). Use the `currencyPair`
values from this endpoint as canonical pair symbols for all other futures calls.

**Funding cadence:** Settlements occur hourly. Convert `nextFundingRun` from
epoch milliseconds: `datetime.utcfromtimestamp(nextFundingRun / 1000)`.

### Funding rate history — `GET /v1/public/futures/funding/history`

Returns historical funding rates for a single pair, newest first. This is
a **public** endpoint — no credentials or `--subaccount-id` needed. Use this
to look up past funding rates. To see funding payments on your own positions,
use `GET /v1/positions/funding/history` instead (see Account Funding History).

```bash
python3 scripts/valr_request.py GET \
  "/v1/public/futures/funding/history?currencyPair=BTCUSDTPERP&limit=24"
```

**Query parameters** (append to path string):

| Parameter | Required | Description |
|---|---|---|
| `currencyPair` | Yes | Pair symbol, e.g. `BTCUSDTPERP` |
| `limit` | No | Number of records to return. Default and maximum: 100 |
| `skip` | No | Number of records to skip for pagination. Default: 0 |

Response is an array of objects:

| Field | Type | Description |
|---|---|---|
| `currencyPair` | string | Pair symbol |
| `fundingRate` | string (decimal) | Funding rate applied at this settlement |
| `fundingTime` | string | ISO 8601 UTC timestamp of the settlement |

Maximum `limit` is 100. Requesting more returns a `400` validation error.
Use `skip` to page through results beyond the first 100.

## Leverage Configuration

These endpoints manage the leverage tier for your futures positions. They
require authentication and must be scoped to a futures-enabled subaccount.

### Get current leverage — `GET /v1/margin/leverage/{currencyPair}`

Returns the current leverage configuration for a specific perpetual futures
pair on the account.

```bash
python3 scripts/valr_request.py GET /v1/margin/leverage/BTCUSDTPERP \
  --subaccount-id YOUR_SUBACCOUNT_ID
```

**Response:**

```json
{
  "pairSymbol": "BTCUSDTPERP",
  "leverageMultiple": 2,
  "initialMarginFraction": 0.5,
  "maintenanceMarginFraction": 0.25,
  "autoCloseMarginFraction": 0.0083,
  "riskLimit": 1500000,
  "riskLimitCurrency": "USDT"
}
```

Returns the same fields as the public risk limit response above, plus the
currently selected `leverageMultiple`. All numeric fields are JSON `number`
type. Note: `riskLimitValue` is named `riskLimit` in this response.

**Error responses:**
- `400` — Unsupported currency pair (e.g. a spot pair like `BTCUSDT`)
- `404` — Futures/margin not enabled on the account, or no leverage
  configured for the pair

### Set leverage — `PUT /v1/margin/leverage/{currencyPair}`

Changes the leverage tier for a specific pair. The `leverageMultiple` must
be one of the values returned by `GET /v1/public/risklimit/{currencyPair}`.

```bash
python3 scripts/valr_request.py PUT /v1/margin/leverage/BTCUSDTPERP \
  --body '{"leverageMultiple":"5"}' \
  --subaccount-id YOUR_SUBACCOUNT_ID
```

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `leverageMultiple` | string | Yes | The desired leverage multiple. Must be greater than one with a maximum of two decimal places. |

**Note:** The request body sends `leverageMultiple` as a **string** (e.g.
`"5"`), not a number — unlike the GET response which returns it as a number.

**Response:** `202 Accepted` with no body on success.

**Error responses:**
- `400` — Unsupported currency pair or invalid leverage value
- `401` — Missing or invalid API key

**Workflow:** To set leverage safely:
1. Call `GET /v1/public/risklimit/{currencyPair}` to see all valid tiers
2. Pick the desired `leverageMultiple` from the response
3. Call `PUT /v1/margin/leverage/{currencyPair}` with that value as a string
4. Optionally call `GET /v1/margin/leverage/{currencyPair}` to confirm

## Open Positions

### View open positions — `GET /v1/positions/open`

Returns all open futures positions on the account.

```bash
python3 scripts/valr_request.py GET /v1/positions/open \
  --subaccount-id YOUR_SUBACCOUNT_ID
```

**Query parameters** (optional, append to path string):

| Parameter | Required | Description |
|---|---|---|
| `currencyPair` | No | Filter by pair, e.g. `BTCUSDTPERP` |
| `skip` | No | Number of results to skip (default 0) |
| `limit` | No | Maximum results to return (default and max 100) |

**Response** is an array of position objects:

```json
[
  {
    "pair": "BTCUSDTPERP",
    "side": "sell",
    "quantity": "0.0001",
    "realisedPnl": "4.22986947",
    "totalSessionEntryQuantity": "0.0001",
    "totalSessionValue": "7.2018",
    "sessionAverageEntryPrice": "72018",
    "averageEntryPrice": "114351",
    "unrealisedPnl": "-0.0018",
    "updatedAt": "2026-03-20T16:00:00.025Z",
    "createdAt": "2025-08-08T06:14:19.598Z",
    "positionId": "dea1914e-9bfe-5008-28a9-0364428735e4",
    "leverageTier": 2
  }
]
```

| Field | Type | Description |
|---|---|---|
| `pair` | string | Pair symbol, e.g. `BTCUSDTPERP` |
| `side` | string | `"buy"` (long) or `"sell"` (short) |
| `quantity` | string (decimal) | Size of the position in the base currency |
| `averageEntryPrice` | string (decimal) | Average entry price across all fills for this position |
| `sessionAverageEntryPrice` | string (decimal) | Average entry price for the current session |
| `totalSessionEntryQuantity` | string (decimal) | Total quantity entered during the current session |
| `totalSessionValue` | string (decimal) | Total notional value of the position (quantity × mark price) |
| `unrealisedPnl` | string (decimal) | Unrealised profit/loss based on current mark price |
| `realisedPnl` | string (decimal) | Realised profit/loss from funding and partial closes |
| `createdAt` | string | ISO 8601 UTC timestamp when the position was opened |
| `updatedAt` | string | ISO 8601 UTC timestamp of the last PnL or funding update |
| `positionId` | string | Unique identifier for this position lifecycle |
| `leverageTier` | number | The leverage tier in use for this position (e.g. `2` for 2x) |

**Note:** This endpoint uses the field name `pair` (not `currencyPair`).

**Note (main account keys):** Calling without `--subaccount-id` silently
returns `[]` rather than an error. Always scope this call to the correct
subaccount.

## Closed Positions

Two endpoints provide different views of closed futures positions.

### Closed positions detail — `GET /v1/positions/closed`

Returns individual close events with per-close details (close price, close
type, fees). A single position lifecycle may have multiple close events if
it was partially closed.

```bash
python3 scripts/valr_request.py GET /v1/positions/closed \
  --subaccount-id YOUR_SUBACCOUNT_ID
```

**Query parameters** (optional):

| Parameter | Required | Description |
|---|---|---|
| `currencyPair` | No | Filter by pair, e.g. `BTCUSDTPERP` |
| `skip` | No | Number of results to skip (default 0) |
| `limit` | No | Maximum results to return (default and max 100) |

**Response** is an array of closed position events:

| Field | Type | Description |
|---|---|---|
| `currencyPair` | string | Pair symbol, e.g. `BTCUSDTPERP` |
| `orderSide` | string | `"buy"` or `"sell"` — the side of the position that was closed |
| `quantity` | string (decimal) | Quantity closed in this event |
| `averageEntryPrice` | string (decimal) | Average entry price of the position |
| `closePrice` | string (decimal) | Price at which this portion was closed |
| `realisedPnl` | string (decimal) | Realised PnL from this close event |
| `closeType` | string | How the position was closed: `"Trade"`, `"Liquidation"`, or `"Adl"` (auto-deleveraging) |
| `fees` | string (decimal) | Trading fees incurred on the close |
| `createdAt` | string | ISO 8601 UTC timestamp of the close event |
| `positionId` | string | Position lifecycle identifier |

### Closed positions summary — `GET /v1/positions/closed/summary`

Returns a per-position summary aggregating all close events for each
position lifecycle.

```bash
python3 scripts/valr_request.py GET /v1/positions/closed/summary \
  --subaccount-id YOUR_SUBACCOUNT_ID
```

This endpoint accepts **no query parameters**.

**Response** is an array of position summaries:

| Field | Type | Description |
|---|---|---|
| `currencyPair` | string | Pair symbol |
| `side` | string | `"buy"` or `"sell"` |
| `quantity` | string (decimal) | Total quantity closed |
| `averageEntryPrice` | string (decimal) | Average entry price |
| `averageClosePrice` | string (decimal) | Weighted average close price across all close events |
| `realisedPnl` | string (decimal) | Total realised PnL for this position |
| `fees` | string (decimal) | Total fees across all close events |
| `positionCreatedAt` | string | When the position was originally opened |
| `positionId` | string | Position lifecycle identifier |

**When to use which:**
- `/v1/positions/closed` — per-close granularity (partial closes, distinguishing trade vs liquidation)
- `/v1/positions/closed/summary` — one row per position with aggregated totals

## Position History

### Position lifecycle events — `GET /v1/positions/history`

Returns a chronological log of all state changes for positions on a specific
pair (opening, increasing, reducing, PnL settlements, closing).

```bash
python3 scripts/valr_request.py GET \
  "/v1/positions/history?currencyPair=BTCUSDTPERP" \
  --subaccount-id YOUR_SUBACCOUNT_ID
```

**Query parameters:**

| Parameter | Required | Description |
|---|---|---|
| `currencyPair` | Yes | Pair symbol, e.g. `BTCUSDTPERP` |

No `skip`, `limit`, or date filtering. Returns all available history for the
specified pair.

**Response** is an array of position events, newest first:

| Field | Type | Description |
|---|---|---|
| `updateType` | string | Type of position event (see table below) |
| `currencyPair` | string | Pair symbol |
| `side` | string | `"buy"` or `"sell"` |
| `quantity` | string (decimal) | Position size after this event |
| `realisedPnl` | string (decimal) | Cumulative realised PnL at this point |
| `totalSessionEntryQuantity` | string (decimal) | Session entry quantity |
| `totalSessionValue` | string (decimal) | Session value (quantity × mark price) |
| `sessionAverageEntryPrice` | string (decimal) | Session average entry price |
| `averageEntryPrice` | string (decimal) | Overall average entry price |
| `updatedAt` | string | ISO 8601 UTC timestamp of this event |
| `positionId` | string | Position lifecycle identifier |

**Update types:**

| `updateType` | Description |
|---|---|
| `New` | Position opened |
| `Increase` | Position size increased (added to existing position) |
| `Reduce` | Position size reduced by a trade |
| `Adl Reduce` | Position reduced by auto-deleveraging |
| `Remove` | Position fully closed |
| `Pnl` | Hourly PnL and funding settlement update |

**Note:** `Pnl` events occur every hour (aligned with funding settlements),
so this endpoint can return many entries for long-lived positions. Filter
client-side if you only need recent events.

## Account Funding History

### Funding payments — `GET /v1/positions/funding/history`

Returns funding payments the account has paid or received. Distinct from the
**public** `GET /v1/public/futures/funding/history` — this shows actual
amounts for your specific positions.

```bash
python3 scripts/valr_request.py GET \
  "/v1/positions/funding/history?currencyPair=BTCUSDTPERP" \
  --subaccount-id YOUR_SUBACCOUNT_ID
```

**Query parameters:**

| Parameter | Required | Description |
|---|---|---|
| `currencyPair` | Yes | Pair symbol, e.g. `BTCUSDTPERP` |
| `startTime` | No | Start of date range, ISO 8601 UTC (e.g. `2025-01-01T00:00:00.000Z`) |
| `endTime` | No | End of date range, ISO 8601 UTC |
| `skip` | No | Number of results to skip (default 0) |
| `limit` | No | Maximum results to return (default and max 100) |

Without `startTime`/`endTime`, returns the last 30 days by default.

**Response** is an array of funding events, newest first:

```json
[
  {
    "currencyPair": "BTCUSDTPERP",
    "side": "sell",
    "createdAt": "2026-03-06T10:00:00.144Z",
    "fundingRate": "-0.00046",
    "fundingAmount": "-0.0033",
    "positionTotal": "7.15",
    "positionId": "dea1914e-9bfe-5008-28a9-0364428735e4"
  }
]
```

| Field | Type | Description |
|---|---|---|
| `currencyPair` | string | Pair symbol |
| `side` | string | `"buy"` (long) or `"sell"` (short) |
| `createdAt` | string | ISO 8601 UTC timestamp of the funding settlement |
| `fundingRate` | string (decimal) | The funding rate applied at this settlement |
| `fundingAmount` | string (decimal) | Amount paid or received. **Negative = paid, positive = received.** |
| `positionTotal` | string (decimal) | Position notional value at the time of funding (quantity × mark price) |
| `positionId` | string | Position lifecycle identifier |

**Interpreting funding amounts:**
- **Positive** `fundingAmount` = account received funding
- **Negative** `fundingAmount` = account paid funding
- The sign of `fundingAmount` is the definitive indicator — do not infer
  direction from `fundingRate` and `side` independently. The API has already
  applied rate, side, and size to produce the final signed amount.

**Pagination:** `skip` and `limit`. Maximum `limit` is 100.
