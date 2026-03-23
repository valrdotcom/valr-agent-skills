# History Reference

> **Always call the API.** Do not answer from the examples in this file —
> call the endpoint via `valr_request.py` every time.

## Permissions

- **View** — required for all endpoints in this file

## Overview

| What you want | Endpoint |
|---|---|
| Your executed trades (fills), with fees | `GET /v1/account/tradehistory` or `GET /v1/account/{pair}/tradehistory` |
| Your past orders and their outcomes | `GET /v1/orders/history` |
| State transitions for a single order | `GET /v1/orders/history/detail/orderid/{id}` |
| Full account ledger (trades, deposits, fees, etc.) | `GET /v1/account/transactionhistory` |

> **Order history summary** (aggregated totals for a single known order ID) is
> already documented in `references/trading.md` under "Check Order Status".

---

## Pagination

All history endpoints return at most 100 records. If 100 are returned,
more may exist — offer to page. Use `beforeId` (cursor, preferred) or
`skip` (offset). Paginate until fewer than `limit` records are returned.

- **Do not state the count as a total.** Tell the user how many were returned and that more may exist.
- To determine a true total, paginate exhaustively. Warn the user this may require many requests; suggest narrowing with `startTime`/`endTime` first.

---

## Account Trade History (Fills)

- Each record represents a trade that executed against your order.
- `price` and `total` are in the pair's **quote currency** (e.g. USDT for `BTCUSDT`, BTC for `ETHBTC`). For cross-currency aggregation, see `references/market-data.md`.

### All pairs

`GET /v1/account/tradehistory`

Supports date filtering and cursor-based backwards pagination.

**Query parameters:**

| Parameter | Type | Notes |
|---|---|---|
| `skip` | integer | Records to skip. Default: 0 |
| `limit` | integer | Records to return. Default and max: 100 |
| `startTime` | string | ISO 8601 UTC (e.g. `2024-01-01T00:00:00.000Z`). Filter by `tradedAt`. |
| `endTime` | string | ISO 8601 UTC. Filter by `tradedAt`. |
| `beforeId` | string | Return records before this trade `id`. Use for cursor-based backwards pagination. |

**Example:**

```bash
# Most recent 100 fills
python3 scripts/valr_request.py GET /v1/account/tradehistory

# Fills for a date range
python3 scripts/valr_request.py GET "/v1/account/tradehistory?startTime=2024-01-01T00:00:00.000Z&endTime=2024-01-31T23:59:59.999Z"

# Next page (backwards from a known trade ID)
python3 scripts/valr_request.py GET "/v1/account/tradehistory?beforeId=0197d496-0e9f-7230-9aa1-4699655e7230"
```

**Response** — array of fill objects:

```json
[
  {
    "id": "0197d496-0e9f-7230-9aa1-4699655e7230",
    "orderId": "0197d496-0e4e-7453-ae5b-1d930e8f3a81",
    "currencyPair": "BTCUSDT",
    "price": "93129",
    "quantity": "0.0001",
    "side": "buy",
    "fee": "0.0000001",
    "feeCurrency": "BTC",
    "tradedAt": "2024-06-13T09:21:48.393Z",
    "sequenceId": 1368928567986636000,
    "customerOrderId": "my-order-001"
  }
]
```

| Field | Notes |
|---|---|
| `id` | Trade (fill) ID — use as `beforeId` for the next page |
| `orderId` | The order that produced this fill |
| `side` | Lowercase: `"buy"` or `"sell"` |
| `fee` | Fee charged for this fill (may be absent if zero) |
| `feeCurrency` | Currency the fee was deducted in |
| `makerReward` / `makerRewardCurrency` | Maker rebate, if applicable |
| `customerOrderId` | Only present if you set one when placing the order |

### Single pair

`GET /v1/account/{currencyPair}/tradehistory`

No date filtering. Returns up to 100 fills for the given pair.

**Query parameters:**

| Parameter | Type | Notes |
|---|---|---|
| `skip` | integer | Default: 0 |
| `limit` | integer | Default and max: 100 |

**Example:**

```bash
python3 scripts/valr_request.py GET /v1/account/BTCUSDT/tradehistory
```

Response schema is identical to the all-pairs endpoint above.

---

## Order History (List)

`GET /v1/orders/history`

- Paginated list of past orders, filtered by `orderUpdatedAt`.
- Use to browse historical orders, check outcomes, and review fill totals.

**Query parameters:**

| Parameter | Type | Notes |
|---|---|---|
| `skip` | integer | Default: 0 |
| `limit` | integer | Default and max: 100 |
| `currencyPair` | string | Filter to a specific pair, e.g. `BTCUSDT` |
| `statuses` | string | Comma-separated. Valid values: `PLACED`, `FILLED`, `CANCELLED`, `FAILED`, `ACTIVE`, `PARTIALLY_FILLED`, `EXPIRED`, `PARTIALLY_FILLED_DUE_TO_SLIPPAGE`, `ORDER_MODIFIED` |
| `startTime` | string | ISO 8601 UTC — filter by `orderUpdatedAt` |
| `endTime` | string | ISO 8601 UTC — filter by `orderUpdatedAt` |
| `excludeFailures` | boolean | `true` to hide failed orders. Default: `false` |
| `showZeroVolumeCancels` | boolean | `true` to include cancelled orders with no fills. Default: `false` |

**Examples:**

```bash
# All recent orders
python3 scripts/valr_request.py GET /v1/orders/history

# Filled BTCUSDT orders only
python3 scripts/valr_request.py GET "/v1/orders/history?currencyPair=BTCUSDT&statuses=FILLED"

# Orders updated in a date range
python3 scripts/valr_request.py GET "/v1/orders/history?startTime=2024-01-01T00:00:00.000Z&endTime=2024-01-31T23:59:59.999Z"
```

**Response** — array of order summary objects:

```json
[
  {
    "orderId": "612ca8ef-15a3-4a85-b991-cc8d23c0e485",
    "customerOrderId": "my-order-001",
    "orderStatusType": "Filled",
    "currencyPair": "BTCUSDT",
    "orderSide": "buy",
    "orderType": "limit",
    "originalPrice": "93129",
    "averagePrice": "93129",
    "originalQuantity": "0.0001",
    "totalExecutedQuantity": "0.0001",
    "remainingQuantity": "0",
    "total": "9.3129",
    "totalFee": "0.0000001",
    "feeCurrency": "BTC",
    "timeInForce": "GTC",
    "failedReason": "",
    "orderCreatedAt": "2024-06-13T09:21:00.000Z",
    "orderUpdatedAt": "2024-06-13T09:21:48.393Z"
  }
]
```

Key fields:

| Field | Notes |
|---|---|
| `orderStatusType` | Final status: `"Filled"`, `"Cancelled"`, `"Failed"`, `"Partially Filled"`, etc. |
| `averagePrice` | Weighted average fill price (string; `"0"` if unfilled) |
| `totalExecutedQuantity` | Base amount actually filled |
| `total` | Total quote amount executed |
| `totalFee` | Aggregate fee across all fills |
| `remainingQuantity` | Unfilled base quantity |
| `stopPrice` | Present for stop-loss / take-profit orders |

---

## Order Status Detail (State Transitions)

`GET /v1/orders/history/detail/orderid/{orderId}`
`GET /v1/orders/history/detail/customerorderid/{customerOrderId}`

- Returns every state transition an order went through — useful for debugging or auditing.
- **No query parameters.** The ID is a path segment.

**Response** — array of status snapshot objects. **Index 0 is the most recent state (reverse-chronological).** When presenting to a user, reverse for oldest-to-newest, but always tell the user the raw API order is reverse-chronological.

> **REQUIRED:** Always explicitly inform the user that the raw API returns index 0 as the most recent state (reverse-chronological), even when you present transitions chronologically.

```bash
python3 scripts/valr_request.py GET /v1/orders/history/detail/orderid/612ca8ef-15a3-4a85-b991-cc8d23c0e485
```

```json
[
  {
    "orderId": "612ca8ef-15a3-4a85-b991-cc8d23c0e485",
    "orderStatusType": "Filled",
    "currencyPair": "BTCUSDT",
    "orderSide": "buy",
    "orderType": "limit",
    "originalPrice": "93129",
    "originalQuantity": "0.0001",
    "remainingQuantity": "0",
    "executedPrice": "93129",
    "executedQuantity": "0.0001",
    "executedFee": "0.0000001",
    "timeInForce": "GTC",
    "customerOrderId": "my-order-001",
    "orderCreatedAt": "2024-06-13T09:21:00.000Z",
    "orderUpdatedAt": "2024-06-13T09:21:48.393Z"
  },
  {
    "orderId": "612ca8ef-15a3-4a85-b991-cc8d23c0e485",
    "orderStatusType": "Placed",
    "executedPrice": "0",
    "executedQuantity": "0",
    "executedFee": "0",
    ...
  }
]
```

Key fields (per snapshot):

| Field | Notes |
|---|---|
| `executedPrice` | Price at which *this* execution event occurred |
| `executedQuantity` | Base quantity executed *in this event* |
| `executedFee` | Fee charged *for this event* |
| `orderStatusType` | Status at this snapshot: `"Placed"`, `"Filled"`, `"Cancelled"`, `"Failed"`, `"Partially Filled"`, `"Active"` |

> Unlike `history/summary`, this endpoint works for **all** order states including still-active orders. For aggregate totals (`averagePrice`, `totalFee`, etc.) use `GET /v1/orders/history/summary/orderid/{id}` (see `references/trading.md`).

---

## Account Transaction History

`GET /v1/account/transactionhistory`

- Full account ledger: every debit and credit including trades, deposits, withdrawals, fees, and referral rebates.
- Use for an accounting-level view of account activity.

**Query parameters:**

| Parameter | Type | Notes |
|---|---|---|
| `skip` | integer | Default: 0 |
| `limit` | integer | Default and max: 100 |
| `currency` | string | Filter by currency, e.g. `BTC`, `USDT` |
| `transactionTypes` | string | Comma-separated type codes — see below |
| `startTime` | string | ISO 8601 UTC |
| `endTime` | string | ISO 8601 UTC |
| `beforeId` | string | Cursor-based backwards pagination (use the `id` of the oldest record) |

**Supported `transactionTypes` values:**

| Type code | Description |
|---|---|
| `LIMIT_BUY` | Limit buy order fill |
| `LIMIT_SELL` | Limit sell order fill |
| `MARKET_BUY` | Market buy order fill |
| `MARKET_SELL` | Market sell order fill |
| `SIMPLE_BUY` | Simple buy order |
| `SIMPLE_SELL` | Simple sell order |
| `AUTO_BUY` | Auto-buy order |
| `MAKER_REWARD` | Maker fee rebate |
| `BLOCKCHAIN_RECEIVE` | Incoming on-chain cryptocurrency deposit |
| `BLOCKCHAIN_SEND` | Outgoing on-chain cryptocurrency withdrawal |
| `FIAT_DEPOSIT` | Fiat deposit |
| `FIAT_WITHDRAWAL` | Fiat withdrawal |
| `FIAT_WITHDRAWAL_REVERSAL` | Fiat withdrawal reversal |
| `FIAT_WITHDRAWAL_FEE_REVERSAL` | Fiat withdrawal fee reversal |
| `CREDIT_CARD_DEPOSIT` | Credit card deposit |
| `OFF_CHAIN_BLOCKCHAIN_WITHDRAW` | Off-chain crypto withdrawal |
| `OFF_CHAIN_BLOCKCHAIN_DEPOSIT` | Off-chain crypto deposit |
| `REFERRAL_REBATE` | Referral programme rebate |
| `REFERRAL_REWARD` | Referral reward |
| `PROMOTIONAL_REBATE` | Promotional rebate |
| `INTERNAL_TRANSFER` | Internal transfer between subaccounts |
| `PAYMENT_SENT` | Payment sent |
| `PAYMENT_RECEIVED` | Payment received |
| `PAYMENT_REVERSED` | Payment reversal |
| `PAYMENT_REWARD` | Payment reward |
| `SIMPLE_SWAP_BUY` | Simple swap buy |
| `SIMPLE_SWAP_SELL` | Simple swap sell |
| `SIMPLE_SWAP_FAILURE_REVERSAL` | Simple swap failure reversal |
| `ACCOUNT_FUNDING` | Account funding |
| `FUND` | Fund |
| `SPOT_BORROW_INTEREST_CHARGE` | Spot borrow interest charge |
| `SPOT_LEND_INTEREST_PAYMENT` | Spot lend interest payment |

**Example:**

```bash
# Recent transactions
python3 scripts/valr_request.py GET /v1/account/transactionhistory

# BTC transactions only
python3 scripts/valr_request.py GET "/v1/account/transactionhistory?currency=BTC"

# On-chain BTC deposits and withdrawals
python3 scripts/valr_request.py GET "/v1/account/transactionhistory?currency=BTC&transactionTypes=BLOCKCHAIN_RECEIVE,BLOCKCHAIN_SEND"

# Limit and market trade fills only
python3 scripts/valr_request.py GET "/v1/account/transactionhistory?transactionTypes=LIMIT_BUY,LIMIT_SELL,MARKET_BUY,MARKET_SELL"
```

**Response** — array of transaction objects:

```json
[
  {
    "id": "0197d496-0e9f-7ef5-8476-c45cd13ccef5",
    "transactionType": {
      "type": "TRADE",
      "description": "Trade"
    },
    "debitCurrency": "USDT",
    "debitValue": "9.3129",
    "creditCurrency": "BTC",
    "creditValue": "0.0001",
    "feeCurrency": "BTC",
    "feeValue": "0.0000001",
    "eventAt": "2024-06-13T09:21:48.393Z",
    "additionalInfo": {
      "currencyPairSymbol": "BTCUSDT",
      "orderId": "612ca8ef-15a3-4a85-b991-cc8d23c0e485"
    }
  }
]
```

| Field | Notes |
|---|---|
| `transactionType.type` | Machine-readable type code |
| `debitCurrency` / `debitValue` | What left your account (absent for credit-only events) |
| `creditCurrency` / `creditValue` | What entered your account (absent for debit-only events) |
| `feeCurrency` / `feeValue` | Fee, if applicable |
| `eventAt` | ISO 8601 timestamp |
| `additionalInfo` | Context-dependent — may include `orderId`, `currencyPairSymbol`, `costPerCoin`, etc. |
