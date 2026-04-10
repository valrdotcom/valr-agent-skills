# Trading Reference

> **Always call the API.** Do not answer from the examples in this file —
> call the endpoint via `{baseDir}/scripts/valr_request.py` every time.

## Permissions

- **View** — required to read open orders and order status
- **Trade** — required to place and cancel orders

## Quick Reference

> **Read the full section for any operation before calling the endpoint.**
> The table below is a routing aid — it does not show required fields,
> body schemas, or response formats. Each section below has critical details
> that affect correctness (e.g. which fields go in the path vs body).

| Operation | Endpoint | Key Detail |
|---|---|---|
| Place limit | `POST /v2/orders/limit` | Body: side, quantity, price, pair |
| Place market | `POST /v2/orders/market` | Body: side, pair, baseAmount OR quoteAmount |
| Place stop-limit | `POST /v2/orders/stop/limit` | Body includes stopPrice + type |
| Place simple | `POST /v1/simple/{pair}/order` | Body: side, payInCurrency, payAmount |
| List open orders | `GET /v1/orders/open` | Returns all pairs |
| Check active order | `GET /v1/orders/{pair}/orderid/{id}` | Pair is required in path |
| Check completed order | `GET /v1/orders/history/summary/orderid/{id}` | Use when active returns 404 |
| Cancel one order | `DELETE /v2/orders/order` | Body: `{"orderId":"...","pair":"..."}` — not a path-segment delete |
| Cancel all (pair) | `DELETE /v1/orders/{pair}` | No body needed |
| Cancel all | `DELETE /v1/orders` | No body needed |
| Modify an order | `PUT /v2/orders/modify` | Body: orderId, pair, modifyMatchStrategy |
| Place batch orders | `POST /v1/batch/orders` | Up to 20 ops; mix place, cancel, modify |

## Place a Limit Order

`POST /v2/orders/limit` — synchronous; returns `201 Created` with the new order
ID once the order is accepted by the matching engine.

> A v1 endpoint (`POST /v1/orders/limit`) also exists and returns `202 Accepted`
> asynchronously. Prefer v2 for agentic use — you get an immediate confirmation.

**Before placing, read the pair constraints** from
`GET /v1/public/pairs` (see `{baseDir}/references/market-data.md`) to check:
- `minBaseAmount` / `maxBaseAmount` — quantity limits
- `minQuoteAmount` / `maxQuoteAmount` — total order value limits (price × quantity)
- `tickSize` — minimum price increment; price must be a multiple of this value

**Request body:**

```json
{
  "side": "BUY",
  "quantity": "0.001",
  "price": "50000",
  "pair": "BTCUSDT",
  "postOnly": false,
  "timeInForce": "GTC",
  "customerOrderId": "my-order-001"
}
```

| Field | Required | Notes |
|---|---|---|
| `side` | Yes | `"BUY"` or `"SELL"` (uppercase) |
| `quantity` | Yes | Base currency amount, as a string |
| `price` | Yes | Quote currency price, as a string; must be a multiple of `tickSize` |
| `pair` | Yes | Currency pair symbol, e.g. `"BTCUSDT"` |
| `postOnly` | No | `true` places a post-only limit (maker-only); cancels if it would immediately fill |
| `timeInForce` | No | `"GTC"` (default), `"FOK"`, or `"IOC"` — see below |
| `customerOrderId` | No | Your own reference ID — recommended; see constraints below |

**Time-in-force options:**

- `GTC` (Good Till Cancelled) — order rests on the book until filled or explicitly cancelled
- `FOK` (Fill or Kill) — must fill completely in full immediately, or it is cancelled entirely; no partial fills
- `IOC` (Immediate or Cancel) — fills as much as possible immediately; any unfilled remainder is cancelled (partial fill is possible)

**Fee implications:** A limit order may pay maker or taker fees depending on whether it crosses the spread at placement time. A `GTC` order that does not immediately match rests on the book; any fill or partial fill that occurs later pays the **maker** fee. An order that crosses the spread immediately pays the **taker** fee. For your current rates, see `{baseDir}/references/fees.md`.

**Successful response (`201 Created`):**

```json
{ "id": "019cced5-85ab-7111-a0a6-f3a87b3c40aa" }
```

The `id` is the system-assigned order UUID. Store this for status lookups and cancellation.

### `customerOrderId` constraints

- Alphanumeric characters and hyphens only (no spaces or special characters)
- Maximum 50 characters
- Must be unique across all currently open orders on the account

## Place a Market Order

`POST /v2/orders/market` — executes immediately at the best available price.
Market orders are always `IOC` (Immediate or Cancel): they fill as much as
possible and any unfilled remainder is cancelled. Returns `201 Created`.

> Not all pairs support market orders. Check `GET /v1/public/{pair}/ordertypes`
> first — `MARKET` must be in the list. See `{baseDir}/references/market-data.md`.

**Before placing, check pair constraints** (`GET /v1/public/pairs`) for
`minBaseAmount` and `minQuoteAmount`.

**Request body:**

```json
{
  "side": "BUY",
  "quoteAmount": "100",
  "pair": "BTCUSDT"
}
```

| Field | Required | Notes |
|---|---|---|
| `side` | Yes | `"BUY"` or `"SELL"` (uppercase) |
| `pair` | Yes | Currency pair symbol, e.g. `"BTCUSDT"` |
| `baseAmount` | One of | Amount of base currency to trade (e.g. BTC) |
| `quoteAmount` | One of | Amount of quote currency to trade (e.g. USDT) |

Specify exactly one of `baseAmount` or `quoteAmount` — not both. Use
`baseAmount` when you want to trade a fixed amount of the base currency; use
`quoteAmount` when you want to spend or receive a fixed amount of the quote
currency. Both fields work for both BUY and SELL.

**Fee implications:** Market orders always pay the **taker** fee — they fill
immediately against existing orders on the book. For your current rate, see
`{baseDir}/references/fees.md`.

**Successful response (`201 Created`):**

```json
{ "id": "019ccefa-3b7e-73a5-99e2-73a147e9e3a4" }
```

**If liquidity is insufficient** the order may return a `Failed` status with
`failedReason` explaining the slippage rejection. Check order history
(`GET /v1/orders/history/summary/orderid/{id}`) to confirm the outcome.

## Place a Stop-Loss or Take-Profit Order

`POST /v2/orders/stop/limit` — places a conditional limit order that sits
inactive until the market price reaches `stopPrice`, at which point a limit
order at `price` is placed. Returns `201 Created`.

Two order types share this endpoint, distinguished by the `type` field:

- **`STOP_LOSS_LIMIT`** — triggers when price *falls to* `stopPrice`. Typically
  used to cap downside on a long position (sell if price drops too far).
- **`TAKE_PROFIT_LIMIT`** — triggers when price *rises to* `stopPrice`. Typically
  used to lock in gains on a long position (sell once a target price is reached).

> Check `GET /v1/public/{pair}/ordertypes` to confirm the pair supports
> `STOP_LOSS_LIMIT` / `TAKE_PROFIT_LIMIT` before placing.

**Request body:**

```json
{
  "side": "SELL",
  "quantity": "0.001",
  "price": "49000",
  "stopPrice": "50000",
  "pair": "BTCUSDT",
  "type": "STOP_LOSS_LIMIT",
  "timeInForce": "GTC"
}
```

| Field | Required | Notes |
|---|---|---|
| `side` | Yes | `"BUY"` or `"SELL"` (uppercase) |
| `quantity` | Yes | Base currency amount, as a string |
| `price` | Yes | Limit price at which the order executes once triggered, as a string |
| `stopPrice` | Yes | Market price that triggers the order, as a string |
| `pair` | Yes | Currency pair symbol, e.g. `"BTCUSDT"` |
| `type` | Yes | `"STOP_LOSS_LIMIT"` or `"TAKE_PROFIT_LIMIT"` |
| `timeInForce` | No | `"GTC"` (default) |
| `customerOrderId` | No | Your own reference ID — see constraints under Place a Limit Order |

**Successful response (`201 Created`):**

```json
{ "id": "019ccf14-7eb6-75e0-aac5-f30921223982" }
```

**Status** — while waiting to trigger, `orderStatusType` is `"Active"` (not
`"Placed"`). The `stopPrice` field appears alongside `originalPrice` (the limit
price) in both the open orders list and the status endpoint. `orderType` in
responses is `"stop-loss-limit"` or `"take-profit-limit"` (lowercase, hyphenated).

**Cancellation** — use the same `DELETE /v2/orders/order` endpoint as for
limit orders.

## List Open Orders

`GET /v1/orders/open` — returns all open orders across all pairs.

**Response** — array of order objects:

```json
[
  {
    "orderId": "019cced5-85ab-7111-a0a6-f3a87b3c40aa",
    "side": "buy",
    "remainingQuantity": "0.0001",
    "price": "50000",
    "currencyPair": "BTCUSDT",
    "createdAt": "2026-03-08T19:03:45.835Z",
    "originalQuantity": "0.0001",
    "filledPercentage": "0.00",
    "customerOrderId": "my-order-001",
    "updatedAt": "2026-03-08T19:03:45.837Z",
    "status": "Placed",
    "type": "limit",
    "timeInForce": "GTC",
    "allowMargin": false
  }
]
```

Key fields:

| Field | Notes |
|---|---|
| `orderId` | System UUID |
| `side` | Lowercase: `"buy"` or `"sell"` |
| `status` | `"Placed"` while resting on the book |
| `type` | `"limit"` or `"post-only limit"` |
| `filledPercentage` | Percentage filled so far (string) |
| `customerOrderId` | Only present if you set one at placement |

## Check Order Status

Use **two different endpoints** depending on whether the order is still active:

### Active (in-progress) orders

`GET /v1/orders/{currencyPair}/orderid/{orderId}`
`GET /v1/orders/{currencyPair}/customerorderid/{customerOrderId}`

**Response:**

```json
{
  "orderId": "019cced5-85ab-7111-a0a6-f3a87b3c40aa",
  "orderStatusType": "Placed",
  "currencyPair": "BTCUSDT",
  "originalPrice": "50000",
  "remainingQuantity": "0.0001",
  "originalQuantity": "0.0001",
  "orderSide": "buy",
  "orderType": "limit",
  "failedReason": "",
  "orderUpdatedAt": "2026-03-08T19:03:45.837Z",
  "orderCreatedAt": "2026-03-08T19:03:45.835Z",
  "customerOrderId": "my-order-001",
  "timeInForce": "GTC"
}
```

Note: field names differ from the open orders list — `orderSide` (not `side`),
`orderType` (not `type`), `orderStatusType` (not `status`), `originalPrice`
(not `price`), `orderCreatedAt`/`orderUpdatedAt` (not `createdAt`/`updatedAt`).

### Completed or cancelled orders

`GET /v1/orders/history/summary/orderid/{orderId}`
`GET /v1/orders/history/summary/customerorderid/{customerOrderId}`

Returns the same fields as above, plus:

| Field | Notes |
|---|---|
| `averagePrice` | Average fill price (string; `"0"` if unfilled) |
| `total` | Total quote amount executed (string) |
| `totalExecutedQuantity` | Base amount actually filled (string) |
| `totalFee` | Fee charged (string) |
| `feeCurrency` | Currency the fee was charged in |

`orderStatusType` will be `"Cancelled"`, `"Filled"`, or `"Partially Filled"`.

> If an order is not found at the active endpoint, try the history endpoint —
> the order may have been filled or cancelled since you last checked.

> To see every state transition an order went through (e.g. Placed → Partially
> Filled → Cancelled), use `GET /v1/orders/history/detail/orderid/{id}` instead.
> This is documented in `{baseDir}/references/history.md`.

## Place a Simple Order

`POST /v1/simple/{currencyPair}/order` — executes immediately at VALR's quoted
price. Simple orders have the widest pair coverage and are the preferred
alternative when a pair does not support `MARKET`. There is no v2 equivalent.

Simple orders are **FOK** (Fill or Kill) — they fill in full immediately or
fail. They never rest on the book, so they cannot be cancelled. Simple orders
always pay a flat fee deducted from the received amount. To preview the fee
and receive amount before placing, use the quote endpoint in
`{baseDir}/references/fees.md`.

> Check `GET /v1/public/{pair}/ordertypes` to confirm the pair supports `SIMPLE`.

**Request body:**

```json
{
  "payInCurrency": "USDT",
  "payAmount": "10",
  "side": "BUY"
}
```

| Field | Required | Notes |
|---|---|---|
| `side` | Yes | `"BUY"` or `"SELL"` (uppercase) |
| `payInCurrency` | Yes | The currency you are spending. For a BUY, use the quote currency (e.g. `"USDT"`). For a SELL, use the base currency (e.g. `"BTC"`). |
| `payAmount` | Yes | How much of `payInCurrency` to spend, as a string |

**Successful response (`202 Accepted`):**

```json
{ "id": "019ccf22-e493-7541-b846-895ab42daef3" }
```

### Checking simple order status

Use `GET /v1/simple/order/{orderId}` — **not** the standard order status
endpoints (`/v1/orders/{pair}/orderid/{id}`). The simple status endpoint returns
a richer response tailored to the pay-in/pay-out framing:

```json
{
  "orderId": "019ccf22-e493-7541-b846-895ab42daef3",
  "success": true,
  "processing": false,
  "paidAmount": "9.9999",
  "paidCurrency": "USDT",
  "receivedAmount": "0.00014239",
  "receivedCurrency": "BTC",
  "feeAmount": "0.00000023",
  "feeCurrency": "BTC",
  "orderExecutedAt": "2026-03-08T20:28:16.496802"
}
```

| Field | Notes |
|---|---|
| `success` | `true` if the order filled; `false` if it failed |
| `processing` | `true` while the order is still executing; poll until `false` |
| `paidAmount` | Actual amount deducted (may differ slightly from `payAmount`) |
| `receivedAmount` | Amount of the other currency received |
| `feeAmount` | Fee charged |
| `orderExecutedAt` | Execution timestamp (no timezone suffix — local server time) |

> The standard order status endpoint (`GET /v1/orders/{pair}/orderid/{id}`) also
> recognises simple orders (returning `orderType: "simple"`) but provides less
> detail. Prefer `/v1/simple/order/{id}` for simple orders.

Simple orders never appear in `GET /v1/orders/open` — they are FOK and have no
resting state.

## Cancel All Open Orders

Two v1 endpoints cover bulk cancellation. Both are synchronous in practice —
the response arrives once the cancellations have taken effect.

> These are **v1-only** endpoints. There are no v2 equivalents.

### Cancel all open orders (all pairs)

`DELETE /v1/orders` — cancels every open regular order on the account.

No request body required.

```bash
python3 {baseDir}/scripts/valr_request.py DELETE /v1/orders
```

**Successful response (`200 OK`):**

```json
[
  { "orderId": "019cd293-e97f-73b3-b0ee-e93bd0133f98" },
  { "orderId": "019cd293-ed0f-72e4-8572-3f4f399fcbe8" }
]
```

Returns an array of objects, one per cancelled order. Each object contains
only the system `orderId` — `customerOrderId` is not echoed back.

If there are no open orders, the response is an empty array `[]`.

### Cancel all open orders for a specific pair

`DELETE /v1/orders/{currencyPair}` — cancels every open regular order for
the given pair.

No request body required. The pair is a path segment.

```bash
python3 {baseDir}/scripts/valr_request.py DELETE /v1/orders/BTCUSDT
```

**Successful response (`200 OK`):**

```json
[
  { "orderId": "019cd292-f89c-7be6-b812-731eee7417f6" }
]
```

Same response shape as the all-pairs endpoint. Returns `[]` if no orders
are open for the pair.

### Notes

- Both endpoints cancel **regular orders only** (limit, market resting,
  stop-limit). Conditional orders (stop-loss, take-profit) are unaffected.
- `customerOrderId` is not included in the response — use the returned
  `orderId` values if you need to confirm individual cancellations via the
  order history endpoint.
- If you need to confirm the outcome, follow up with
  `GET /v1/orders/open` or the order history endpoint.

## Cancel an Order

`DELETE /v2/orders/order` — synchronous; returns `200 OK` once cancelled.

> A v1 endpoint (`DELETE /v1/orders/order`) also exists and returns `202
> Accepted` asynchronously. Prefer v2 for agentic use.

**Request body — by system order ID:**

```json
{ "orderId": "019cced5-85ab-7111-a0a6-f3a87b3c40aa", "pair": "BTCUSDT" }
```

**Request body — by customer order ID:**

```json
{ "customerOrderId": "my-order-001", "pair": "BTCUSDT" }
```

**Successful response (`200 OK`):**

```json
{ "id": "019cced5-85ab-7111-a0a6-f3a87b3c40aa" }
```

When cancelling by `customerOrderId`, the response `id` echoes back the
`customerOrderId` rather than the system UUID.

To view all status transitions after cancellation (e.g. Placed → Cancelled),
use `GET /v1/orders/history/detail/orderid/{id}` — see `{baseDir}/references/history.md`.

## Modify an Order

`PUT /v2/orders/modify` — synchronous; returns `201 Created` once the
modification is processed.

> A v1 endpoint (`PUT /v1/orders/modify`) also exists and returns `202 Accepted`
> asynchronously. Prefer v2 for agentic use — you get an immediate confirmation.

Modify the price, remaining quantity, or total quantity of an open or partially
filled **limit order**. Modified orders retain their original `orderId` — the
audit trail can be viewed via `GET /v1/orders/history/detail/orderid/{id}`
(see `{baseDir}/references/history.md`).

**Request body:**

```json
{
  "orderId": "019cced5-85ab-7111-a0a6-f3a87b3c40aa",
  "pair": "BTCUSDT",
  "modifyMatchStrategy": "RETAIN_ORIGINAL",
  "newPrice": "51000"
}
```

| Field | Required | Notes |
|---|---|---|
| `orderId` | Yes | System UUID of the order to modify |
| `pair` | Yes | Currency pair for the order |
| `modifyMatchStrategy` | Yes | Controls behaviour if modified order would immediately match — see below |
| `newPrice` | No | New limit price, as a string |
| `newRemainingQuantity` | No | New remaining base quantity to be executed, as a string |
| `newTotalQuantity` | No | New total base quantity for the order, as a string |
| `customerOrderId` | No | Update the customer order ID on the modified order |

Specify `newRemainingQuantity` **or** `newTotalQuantity`, not both. At least one
of `newPrice`, `newRemainingQuantity`, or `newTotalQuantity` must be provided.

**`newRemainingQuantity` vs `newTotalQuantity`:**

- `newRemainingQuantity` — sets the remaining (unfilled) quantity directly,
  irrespective of how much has already filled.
- `newTotalQuantity` — sets the total order quantity. The new remaining quantity
  becomes `newTotalQuantity` minus the already-filled quantity. If
  `newTotalQuantity` is less than the filled quantity, the order is cancelled.

### `modifyMatchStrategy`

Controls what happens when the modified price would cause the order to
immediately match against existing orders on the book:

- **`RETAIN_ORIGINAL`** — reject the modification and keep the original order
  unchanged. Use this when you want to guarantee you stay at maker (resting)
  status.
- **`CANCEL_ORIGINAL`** — cancel the original order entirely if the modification
  would cause an immediate match. The order is removed from the book.
- **`REPRICE`** — adjust the order price automatically to the nearest level that
  avoids an immediate match, keeping the order active. Use this when you want to
  get as close as possible to your target price without crossing the spread.

### Queue position behaviour

- **Reducing** remaining or total quantity → retains the order's position in the
  queue at that price level.
- **Increasing** remaining or total quantity → moves the order to the back of the
  queue.
- **Changing the price** (up or down) → moves the order to the back of the queue
  at the new price level.

### Successful response (`201 Created`)

```json
{ "id": "019d15e7-4721-74ac-ac86-39db87197b2a" }
```

The `id` in the response is the modify operation ID, not the order ID. The
original order retains its `orderId`. After modification, the order's
`orderStatusType` becomes `"Order Modified"` when queried via the order status
endpoint.

### Error: no-op modification

If the new values are identical to the current values, the API returns `400`
with error code `-21303`:

```json
{
  "modifyOrderId": "019d15e7-c8d0-729d-8077-daa8877137f7",
  "orderId": "019d15e7-1833-79c7-8321-87e20e1c8373",
  "code": -21303,
  "message": "Modify order would not have modified anything and was cancelled"
}
```

## Batch Orders

`POST /v1/batch/orders` — submit up to **20** order operations in a single
request. Supports placing, cancelling, and modifying orders in one call.
Returns `200 OK` with per-operation outcomes.

> **`200 OK` means the batch was submitted, not that all operations succeeded.**
> Each operation is processed independently — one failure does not affect the
> others. Always check each outcome in the response.

**Request body:**

```json
{
  "customerBatchId": "my-batch-001",
  "requests": [
    {
      "type": "PLACE_LIMIT",
      "data": {
        "pair": "BTCUSDT",
        "side": "BUY",
        "quantity": "0.001",
        "price": "50000",
        "timeInForce": "GTC",
        "customerOrderId": "leg-1"
      }
    },
    {
      "type": "PLACE_LIMIT",
      "data": {
        "pair": "BTCUSDT",
        "side": "SELL",
        "quantity": "0.001",
        "price": "55000",
        "timeInForce": "GTC",
        "customerOrderId": "leg-2"
      }
    },
    {
      "type": "CANCEL_ORDER",
      "data": {
        "orderId": "019cced5-85ab-7111-a0a6-f3a87b3c40aa",
        "pair": "BTCUSDT"
      }
    }
  ]
}
```

| Field | Required | Notes |
|---|---|---|
| `customerBatchId` | No | Your own tracking ID — alphanumeric and hyphens, max 50 characters |
| `requests` | Yes | Array of operations (max 20) |
| `requests[].type` | Yes | Operation type — see supported types below |
| `requests[].data` | Yes | Operation-specific fields — same as the individual endpoint |

### Supported operation types

| Type | Description | `data` fields |
|---|---|---|
| `PLACE_LIMIT` | Place a limit order | Same fields as `POST /v2/orders/limit` — see [Place a Limit Order](#place-a-limit-order) |
| `PLACE_MARKET` | Place a market order | Same fields as `POST /v2/orders/market` — see [Place a Market Order](#place-a-market-order) |
| `PLACE_STOP_LIMIT` | Place a stop-limit order | Same fields as `POST /v2/orders/stop/limit` — see [Place a Stop-Loss or Take-Profit Order](#place-a-stop-loss-or-take-profit-order) |
| `CANCEL_ORDER` | Cancel an existing order | `orderId` or `customerOrderId` (one, not both) + `pair` |
| `MODIFY_ORDER` | Modify an existing order | Same fields as `PUT /v2/orders/modify` — see [Modify an Order](#modify-an-order) |

### Constraint: `MODIFY_ORDER` cannot appear with `PLACE_*` operations

A batch that contains both `MODIFY_ORDER` and any `PLACE_*` type will reject the
modify operation with error code `-21311`. The place operations still succeed.
To modify and place in the same workflow, use two separate requests.

`MODIFY_ORDER` **can** appear alongside `CANCEL_ORDER` in the same batch.

### Response (`200 OK`)

```json
{
  "batchId": 1485281165544529920,
  "outcomes": [
    {
      "accepted": true,
      "orderId": "019d15e8-172b-714f-bed5-df15015be184",
      "customerOrderId": "leg-1",
      "requestType": "PLACE_LIMIT"
    },
    {
      "accepted": true,
      "orderId": "019d15e8-172c-7d1a-bf01-f361bd15ccf3",
      "customerOrderId": "leg-2",
      "requestType": "PLACE_LIMIT"
    },
    {
      "accepted": false,
      "error": {
        "code": -12007,
        "message": "Minimum order size not met . Minimum amount: 0.00001 BTC, minimum total: 1 USDT"
      }
    }
  ]
}
```

| Field | Notes |
|---|---|
| `batchId` | System-assigned batch identifier (integer) |
| `outcomes` | Array of results in the same order as the input `requests` |
| `outcomes[].accepted` | `true` if the operation succeeded, `false` if it failed |
| `outcomes[].orderId` | System order UUID (present when `accepted` is `true`) |
| `outcomes[].customerOrderId` | Echoed back if you provided one in the request |
| `outcomes[].requestType` | The operation type (e.g. `"PLACE_LIMIT"`, `"CANCEL_ORDER"`) |
| `outcomes[].error` | Error details (present when `accepted` is `false`) — contains `code` and `message` |

### Notes

- Each operation is validated against the same rules as the individual endpoint
  (pair constraints, minimum sizes, order existence for cancels).
- Outcomes are returned in the same sequence as the input requests — use the
  array index to correlate each outcome with its request.
- The `customerBatchId` is for your own tracking only and is not returned in
  the response. Use `batchId` for any server-side reference.
