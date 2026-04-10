# Trading Fees

> **Always call the API.** Do not answer fee questions from the examples in
> this file — call the endpoint via `{baseDir}/scripts/valr_request.py` every time.

This file covers:

- **Exchange trading fees** — maker/taker model, fee tiers, and how to query your rates via `GET /v1/account/fees/trade`
- **Simple Buy/Sell fees** — flat fee structure and pre-trade quotes via `POST /v1/simple/{pair}/quote`
- **Fee fields in trade history** — how fees and rebates appear in fill records

## Overview

VALR has two distinct fee structures:

- **Exchange trading fees** — maker/taker fees that apply when trading on the
  order book (limit, market, and stop orders). Covered in full below.
- **Simple Buy/Sell fees** — a flat fee that applies to simple orders. Covered
  at the bottom of this file; see `{baseDir}/references/trading.md` for order placement.

---

## Exchange Trading Fees: Maker vs Taker

Every order book trade has two sides: the **maker** and the **taker**.

- **Maker** — your order is placed on the book and waits to be matched by
  someone else. You are *adding* liquidity. Maker fees are lower; at high
  volume tiers they can be zero or **negative** (a rebate — the exchange pays
  you).
- **Taker** — your order immediately matches existing orders on the book. You
  are *removing* liquidity. Taker fees are always higher than maker fees.

### Which order type guarantees which fee?

| Order type | Fee side |
|---|---|
| `LIMIT_POST_ONLY` | Always **maker** — cancelled rather than crossing the spread |
| `MARKET` | Always **taker** — fills immediately against the book |
| `LIMIT` | **Maker** if it rests on the book; **taker** if it fills immediately |
| `STOP_LOSS_LIMIT` / `TAKE_PROFIT_LIMIT` | Same as `LIMIT` once triggered |

Use `LIMIT_POST_ONLY` when you want certainty that you pay the maker rate.

---

## Fee Tiers

Exchange trading fees (maker/taker) are tiered by trading volume — higher
volume earns lower rates. Maker rates decrease faster than taker rates as
volume grows; at high enough volume, maker rates reach 0% or go negative
(the exchange pays you a rebate). Simple Buy/Sell fees are flat and not
subject to volume tiers.

The rates returned by `GET /v1/account/fees/trade` already reflect your
current tier — what you receive is your effective rate, not a pre-discount
rate. To see the full tier table or determine which tier you are on by name,
check the VALR website or the API docs at docs.valr.com.

---

## Querying Your Current Fee Rates

### `GET /v1/account/fees/trade`

**Authentication:** Required (View permission)

Returns the authenticated account's current fee rates for every pair. Rates
reflect the account's current volume tier — higher trading volume earns lower
rates. When presenting rates to a user, always note that these are their
personal rates based on their volume tier, not generic advertised rates.

**Response:** Array of objects.

| Field | Type | Notes |
|---|---|---|
| `currencyPair` | string | e.g. `"BTCUSDT"` |
| `makerPercentage` | string (optional) | Absent if the pair does not support order book trading |
| `takerPercentage` | string (optional) | Absent if the pair does not support order book trading |
| `simplePercentage` | string (optional) | Absent for perpetual futures pairs |

**Example response (abridged — values are illustrative only, do not use them as actual rates):**

```json
[
  {
    "currencyPair": "BTCUSDT",
    "makerPercentage": "0.08",
    "takerPercentage": "0.1",
    "simplePercentage": "1.6"
  },
  {
    "currencyPair": "ETHUSDT",
    "makerPercentage": "0.08",
    "takerPercentage": "0.1",
    "simplePercentage": "1.6"
  },
  {
    "currencyPair": "BTCUSDTPERP",
    "makerPercentage": "0.03",
    "takerPercentage": "0.06"
  }
]
```

> **Always fetch rates live.** Never quote values from the example above to a
> user — they are illustrative only and will be stale. Always call
> `valr_request.py GET /v1/account/fees/trade` and read from the actual
> response.

### Interpreting the values

- **Values are in percentage points.** `"0.08"` means 0.08%, not 8%.
- **`makerPercentage` can be `"0"` or negative** (e.g. `"-0.01"`). A negative
  value means the exchange pays you a rebate for adding liquidity. When a
  rebate applies to a fill, it appears in trade history as `makerReward` and
  `makerRewardCurrency` rather than `fee` and `feeCurrency` — see
  `{baseDir}/references/history.md`.
- **Absent `makerPercentage`/`takerPercentage`** means the pair is not
  available for order book trading (simple orders only).
- **Absent `simplePercentage`** means the pair does not support simple orders
  (perpetual futures pairs fall into this category).

---

## Fee Fields in Trade History

When a trade executes, the fee charged appears in the fill record. See
`{baseDir}/references/history.md` for the full field list. The key fields are:

- `fee` + `feeCurrency` — the fee deducted (taker, or positive maker fee)
- `makerReward` + `makerRewardCurrency` — present instead of `fee` when the
  maker rate is negative and a rebate was paid to you

---

## Simple Buy/Sell Fees

Simple orders carry a flat fee that applies uniformly across all eligible
pairs. Unlike exchange trading fees, there are no tiers — the same rate
applies regardless of volume. The fee is **deducted from the amount you
receive**, not added on top of what you pay.

Perpetual futures pairs do not support simple orders and have no
`simplePercentage` in the fees response.

For simple order placement, see `{baseDir}/references/trading.md`.

### Querying the simple fee rate

Use `GET /v1/account/fees/trade` (documented above). Read the
`simplePercentage` field for the pair you intend to trade. Values are in
percentage points. Do not hardcode any rate — always fetch it live.

### Getting a pre-trade fee estimate

`POST /v1/simple/{currencyPair}/quote`

**Authentication:** Required (View permission)

Returns an estimate of what you would receive and what fee you would pay for
a given simple order, based on current market conditions. **Does not place an
order.**

**Request body:**

| Field | Required | Notes |
|---|---|---|
| `payInCurrency` | Yes | The currency you are paying with |
| `payAmount` | Yes | The amount you want to spend, as a string |
| `side` | Yes | `"BUY"` or `"SELL"` |

**Response:**

| Field | Notes |
|---|---|
| `currencyPair` | The pair quoted |
| `payAmount` | The amount you will pay |
| `receiveAmount` | The amount you will receive after the fee is deducted |
| `fee` | Fee amount, deducted from the received side |
| `feeCurrency` | Currency the fee is charged in |
| `createdAt` | Timestamp of the quote |
| `ordersToMatch` | Array of `{ price, quantity }` — the order book orders that would fill this trade |
| `slippagePercentage` | Estimated slippage as a percentage string |

**Example response:**

```json
{
  "currencyPair": "BTCUSDT",
  "payAmount": "500",
  "receiveAmount": "0.00527481",
  "fee": "0.00008569",
  "feeCurrency": "BTC",
  "createdAt": "2026-03-15T12:11:06.166928965",
  "ordersToMatch": [
    { "price": "94800", "quantity": "0.00536050" }
  ],
  "slippagePercentage": "0.000042"
}
```

**Important:** The quote reflects current market conditions at the moment it
is fetched. It is a snapshot, not a locked price — the actual execution price
may differ if market conditions change before the order is placed.
