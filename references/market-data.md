# Market Data

> **Always fetch live data.** Do not answer market data questions from the
> examples or tables in this file — call the API via `valr_request.py` every
> time. The examples here illustrate response shape only.

All endpoints in this file are public — no credentials required. They work
without `VALR_API_KEY` or `VALR_API_SECRET` being set.

## Contents

| What you need | Section | Key endpoint |
|---|---|---|
| List all currencies and their details | `references/currencies.md` | `GET /v1/public/currencies` |
| List trading pairs and constraints (tick size, min/max amounts) | Currency Pairs | `GET /v1/public/pairs` |
| Check which order types a pair supports | Order Types | `GET /v1/public/ordertypes` |
| 24-hour price and volume summary | Market Summaries | `GET /v1/public/marketsummary` |
| Historical OHLCV candle data (traded or mark price) | Price Buckets | `GET /v1/public/{pair}/buckets` |
| Convert amounts between currencies | Currency Conversion | *(derived from market summaries)* |
| Live order book depth | Orderbook | `GET /v1/public/{pair}/orderbook` |

## Supported Currencies

For currency details (supported currencies, network types, deposit/withdrawal
availability), see `references/currencies.md`.

---

## Currency Pairs

Retrieve all tradeable currency pairs on VALR, including order size limits,
tick size, and pair type.

```
GET /v1/public/pairs
```

### Usage

```bash
python3 scripts/valr_request.py GET /v1/public/pairs
```

To filter by type (e.g. spot pairs only):

```bash
python3 scripts/valr_request.py GET /v1/public/pairs/SPOT
python3 scripts/valr_request.py GET /v1/public/pairs/FUTURE
```

### Response

Returns an array of currency pair objects.

| Field | Type | Description |
|---|---|---|
| `symbol` | string | Pair symbol, e.g. `"BTCUSDC"` |
| `baseCurrency` | string | The asset being bought or sold, e.g. `"BTC"` |
| `quoteCurrency` | string | The currency used to price the base, e.g. `"USDC"` |
| `shortName` | string | Human-readable name, e.g. `"BTC/USDC"` |
| `active` | boolean | Whether the pair is currently tradeable |
| `minBaseAmount` | string | Minimum order size in base currency |
| `maxBaseAmount` | string | Maximum order size in base currency |
| `minQuoteAmount` | string | Minimum order size in quote currency |
| `maxQuoteAmount` | string | Maximum order size in quote currency |
| `tickSize` | string | Minimum price increment |
| `baseDecimalPlaces` | string | Decimal precision for base currency quantities |
| `marginTradingAllowed` | boolean | Whether margin trading is enabled for this pair |
| `currencyPairType` | string | `"SPOT"` or `"FUTURE"` |
| `initialMarginFraction` | string | Initial margin requirement (margin-enabled pairs only) |
| `maintenanceMarginFraction` | string | Maintenance margin requirement (margin-enabled pairs only) |
| `autoCloseMarginFraction` | string | Auto-close margin threshold (margin-enabled pairs only) |

### Example Response

```json
[
  {
    "symbol": "BTCUSDC",
    "baseCurrency": "BTC",
    "quoteCurrency": "USDC",
    "shortName": "BTC/USDC",
    "active": true,
    "minBaseAmount": "0.0001",
    "maxBaseAmount": "5",
    "minQuoteAmount": "1",
    "maxQuoteAmount": "500000",
    "tickSize": "1",
    "baseDecimalPlaces": "8",
    "marginTradingAllowed": true,
    "currencyPairType": "SPOT",
    "initialMarginFraction": "0.2",
    "maintenanceMarginFraction": "0.1",
    "autoCloseMarginFraction": "0.033333333"
  }
]
```

### Notes

- Only pairs with `active: true` are currently tradeable.
- `tickSize` is the minimum price increment — prices must be a multiple of it.
- `minBaseAmount` and `minQuoteAmount` are enforced on order placement.
- Margin-related fields are only present on margin-enabled pairs.

---

## Order Types

Not all order types are supported on all currency pairs. Always check which
types are available for a specific pair before placing an order.

### Order type definitions

| Type | When to use |
|---|---|
| `LIMIT` | Buy or sell at a specific price or better. The order rests on the book until filled or cancelled. |
| `LIMIT_POST_ONLY` | Like a limit order, but guarantees maker execution — the order is cancelled rather than matched if it would fill immediately. Use this to ensure you pay maker fees. |
| `MARKET` | Execute immediately at the best available price. No price control; use when speed matters more than price. Available on a subset of pairs. |
| `SIMPLE` | Market-like immediate execution, designed for pairs where `MARKET` is not supported. Has the widest pair coverage of any order type. |
| `STOP_LOSS_LIMIT` | A limit order that is only submitted to the book when the market price reaches a specified stop price. Used to cap downside — e.g. automatically sell if the price drops to a certain level. |
| `TAKE_PROFIT_LIMIT` | A limit order submitted when the market price reaches a specified stop price. Used to lock in gains — e.g. automatically sell if the price rises to a target level. |

### Get order types for all pairs

```
GET /v1/public/ordertypes
```

No credentials required.

```bash
python3 scripts/valr_request.py GET /v1/public/ordertypes
```

Returns an array of objects, one per currency pair:

| Field | Type | Description |
|---|---|---|
| `currencyPair` | string | Pair symbol, e.g. `"BTCUSDC"` |
| `orderTypes` | array of strings | Supported order type identifiers for this pair |

Example response:

```json
[
  {
    "currencyPair": "BTCUSDC",
    "orderTypes": [
      "LIMIT_POST_ONLY",
      "LIMIT",
      "MARKET",
      "SIMPLE",
      "STOP_LOSS_LIMIT",
      "TAKE_PROFIT_LIMIT"
    ]
  }
]
```

### Get order types for a specific pair

```
GET /v1/public/{currencyPair}/ordertypes
```

No credentials required.

```bash
python3 scripts/valr_request.py GET /v1/public/BTCUSDC/ordertypes
```

Returns a flat array of supported order type strings for the pair:

```json
[
  "LIMIT_POST_ONLY",
  "SIMPLE",
  "MARKET",
  "LIMIT",
  "STOP_LOSS_LIMIT",
  "TAKE_PROFIT_LIMIT"
]
```

### Notes

- Supported order types vary significantly across pairs — always verify before placing an order.
- `SIMPLE` has the broadest coverage and is preferred for immediate execution when `MARKET` is not available.
- `STOP_LOSS_LIMIT` and `TAKE_PROFIT_LIMIT` require both a `stopPrice` (trigger) and a `price` (limit price once triggered).

---

## Market Summaries

Current price and 24-hour statistics for currency pairs.

### All pairs

```
GET /v1/public/marketsummary
```

No credentials required.

```bash
python3 scripts/valr_request.py GET /v1/public/marketsummary
```

Returns an array of market summary objects, one per pair.

### Single pair

```
GET /v1/public/{currencyPair}/marketsummary
```

No credentials required. **Prefer this endpoint over the all-pairs endpoint when the user asks about a specific pair** — do not fetch all pairs and filter client-side.

```bash
python3 scripts/valr_request.py GET /v1/public/BTCUSDC/marketsummary
```

Returns a single market summary object (not an array).

### Response fields

Both endpoints return the same fields:

| Field | Type | Description |
|---|---|---|
| `currencyPair` | string | Pair symbol, e.g. `"BTCUSDC"` |
| `askPrice` | string | Lowest current ask price |
| `bidPrice` | string | Highest current bid price |
| `lastTradedPrice` | string | Price of the most recent trade |
| `previousClosePrice` | string | Closing price from the previous period |
| `baseVolume` | string | 24-hour trading volume in base currency |
| `quoteVolume` | string | 24-hour trading volume in quote currency |
| `highPrice` | string | 24-hour high price |
| `lowPrice` | string | 24-hour low price |
| `created` | string | ISO 8601 timestamp of this snapshot |
| `changeFromPrevious` | string | Percentage change from previous close, e.g. `"-1.12"` means −1.12% |
| `markPrice` | string | Reference price used for perpetual futures; `"0"` for spot pairs |

### Example response (single pair)

```json
{
  "currencyPair": "BTCUSDC",
  "askPrice": "67162",
  "bidPrice": "67120",
  "lastTradedPrice": "67152",
  "previousClosePrice": "67916",
  "baseVolume": "2.50953816",
  "quoteVolume": "168597.2379129",
  "highPrice": "68140",
  "lowPrice": "66814",
  "created": "2026-03-08T15:55:18.385Z",
  "changeFromPrevious": "-1.12",
  "markPrice": "67151"
}
```

### Notes

- The spread between `bidPrice` and `askPrice` reflects the cost of an immediate round-trip trade.
- `changeFromPrevious` is a percentage, not an absolute value. Negative means price has fallen.
- `markPrice` is `"0"` for pairs that only support the `SIMPLE` order type. For other pairs it is a reference price from an external index, used for margin and liquidation calculations.
- When presenting a price, prefer `lastTradedPrice` as the headline figure; surface `bidPrice`/`askPrice` when the user needs to act (buy or sell). Always include `changeFromPrevious` to show the 24-hour price direction.

---

## Price Buckets (OHLCV / Candle Data)

Historical open/high/low/close/volume data for a currency pair, organised into
time buckets. Use for charting, trend analysis, or looking up a price at a
specific point in time.

### Traded price buckets

```
GET /v1/public/{currencyPair}/buckets
```

No credentials required.

> **`startTime` and `endTime` use epoch seconds, not ISO 8601.** This endpoint
> is the exception among VALR public endpoints. Pass a Unix timestamp in
> **seconds** (e.g. `1753102597`), not a datetime string. The mark price buckets
> endpoint below uses ISO 8601 — do not mix them up.

**Parameters:**

| Parameter | Type | Notes |
|---|---|---|
| `currencyPair` | path string | Required. e.g. `BTCUSDT`, `ETHUSDC` |
| `periodSeconds` | integer | Bucket width. Valid values: `60`, `300`, `900`, `1800`, `3600`, `21600`, `86400`. Default: `60` |
| `startTime` | integer | Start of range as **epoch seconds**. Default: `endTime` minus the max number of buckets |
| `endTime` | integer | End of range as **epoch seconds**. Default: current time |
| `limit` | integer | Maximum buckets to return |
| `skip` | integer | Buckets to skip |
| `includeEmpty` | boolean | Include buckets with no trades |

**Period options:**

| `periodSeconds` | Interval |
|---|---|
| `60` | 1 minute |
| `300` | 5 minutes |
| `900` | 15 minutes |
| `1800` | 30 minutes |
| `3600` | 1 hour |
| `21600` | 6 hours |
| `86400` | 1 day |

**Limit:** Maximum 300 buckets per request. A time range exceeding 300 buckets is rejected — narrow the range or use a larger `periodSeconds`.

**Rate limit:** 20 requests/second (higher than the general public endpoint limit).

**Examples:**

```bash
# Last 24 hours of hourly BTCUSDT candles
# startTime = now - 86400 seconds, endTime = now (use shell arithmetic or Python)
python3 -c "import time; print(int(time.time()) - 86400)"  # get startTime

python3 scripts/valr_request.py GET "/v1/public/BTCUSDT/buckets?periodSeconds=3600&startTime=1753102597&endTime=1753188997"

# Daily candles for a specific week
python3 scripts/valr_request.py GET "/v1/public/BTCUSDT/buckets?periodSeconds=86400&startTime=1752096000&endTime=1752700800"
```

**Response** — array of bucket objects:

```json
[
  {
    "currencyPairSymbol": "BTCUSDT",
    "bucketPeriodInSeconds": 3600,
    "startTime": "2024-06-13T09:00:00Z",
    "open": "67100",
    "high": "67350",
    "low": "66950",
    "close": "67200",
    "volume": "1.25340000",
    "quoteVolume": "84218.40"
  }
]
```

| Field | Notes |
|---|---|
| `startTime` | ISO 8601 — start of this bucket's time window (response uses ISO 8601 even though the request parameters use epoch seconds) |
| `open` / `close` | Price at the start and end of the bucket |
| `high` / `low` | Extremes within the bucket |
| `volume` | Base currency volume traded during the bucket |
| `quoteVolume` | Quote currency volume traded during the bucket |

When presenting a single representative price for a bucket, prefer `close`.
Use `(high + low) / 2` when you need a midpoint.

### Mark price buckets

```
GET /v1/public/{currencyPair}/markprice/buckets
```

No credentials required. Returns mark price history — a synthetic reference
calculated as the median of last traded price, best bid, and best ask, derived
from an external market index rather than actual trades on VALR's order book.
**Works for any pair — spot or perpetual.**

> **When presenting mark price data to a user, always explicitly state that the
> values are mark prices, not traded/execution prices.** Mark price differs from
> what you would actually pay or receive in a trade.

Choose between the two bucket endpoints based on what you need:

- **Traded price buckets** (`/buckets`) — actual execution prices on VALR. Authoritative trade record. Includes volume. May show stale prices on illiquid pairs.
- **Mark price buckets** (`/markprice/buckets`) — reference price tracking broader market conditions. Useful for illiquid pairs. No volume data.

**Parameters:** Same as traded price buckets, except:

- `startTime`/`endTime` accept **ISO 8601** datetime strings (e.g. `2025-07-21T08:51:21Z`) instead of epoch seconds.

**Response** — same shape as traded buckets but **without** `volume` and
`quoteVolume`:

```json
[
  {
    "currencyPairSymbol": "BTCUSDT",
    "bucketPeriodInSeconds": 3600,
    "startTime": "2024-06-13T09:00:00Z",
    "open": "67110",
    "high": "67340",
    "low": "66960",
    "close": "67195"
  }
]
```

---

## Currency Conversion

Trade amounts (`price`, `total`) from history endpoints are denominated in the pair's **quote currency**. To aggregate or compare across pairs with different quote currencies, convert using rates from VALR.

### Finding the quote currency of a pair

Use `GET /v1/public/pairs` and look up the pair by symbol — use `quoteCurrency`, do not infer from the symbol string.

### Case 1 — Current rate

Fetch `GET /v1/public/{pair}/marketsummary` and use `lastTradedPrice`.

```bash
python3 scripts/valr_request.py GET /v1/public/BTCUSDT/marketsummary
# → use lastTradedPrice
```

### Case 2 — Historical rate

Fetch `GET /v1/public/{pair}/buckets` scoped to a window covering the trade's timestamp. Use the `close` of the containing bucket.

- `periodSeconds=3600` (1 hour) is a reasonable default.
- Remember: `startTime`/`endTime` for `/buckets` are **epoch seconds**.

```bash
# BTCUSDT rate for the hour covering 2024-06-13 09:21 UTC
python3 scripts/valr_request.py GET \
  "/v1/public/BTCUSDT/buckets?periodSeconds=3600&startTime=1718269200&endTime=1718272800"
# → use close of the bucket whose startTime is "2024-06-13T09:00:00Z"
```

### Finding the bridging pair

Find a pair on VALR where one currency is the base and the other is the quote. Use `GET /v1/public/pairs` and filter by `baseCurrency`/`quoteCurrency`.

| Convert from | Convert to | Bridging pair |
|---|---|---|
| BTC | USDT | `BTCUSDT` (base=BTC, quote=USDT) |
| ETH | USDT | `ETHUSDT` (base=ETH, quote=USDT) |
| ETH | BTC | `ETHBTC` (base=ETH, quote=BTC) |

### Conversion direction

- Source currency is **base** in the bridging pair → **multiply** by the rate.
- Source currency is **quote** in the bridging pair → **divide** by the rate.

**Example** — converting `ETHBTC` trade total of 0.015 BTC to USDT:

1. Trade: `currencyPair: "ETHBTC"`, `total: "0.015"` (BTC)
2. Bridging pair: `BTCUSDT` (base=BTC) → multiply
3. Fetch `BTCUSDT` 1-hour bucket → `close: "67000"`
4. USDT value = `0.015 × 67000 = 1005.00 USDT`

### Precision

Parse rate/amount strings as fixed-point or arbitrary-precision numbers, not IEEE 754 floats, to avoid rounding drift.

### Aggregating across currencies

When aggregating values across pairs with different quote currencies, convert all amounts to the target currency. Do not silently exclude trades that don't match — if exclusion is necessary, state clearly which trades were omitted and why.

### Assumed rates

Prefer fetching a rate from VALR over assuming one. If an assumed rate is used, state it explicitly.

---

## Orderbook

Retrieve the current order book for a currency pair.

```
GET /v1/public/{currencyPair}/orderbook
```

> **URL pattern:** the pair is a path segment *before* `orderbook`, not after.
> Correct: `/v1/public/BTCUSDC/orderbook`
> Wrong: `/v1/public/orderbooks/BTCUSDC` — this path does not exist.

No credentials required.

```bash
python3 scripts/valr_request.py GET /v1/public/BTCUSDC/orderbook
```

### Response

Returns a single object. Note the mixed casing: top-level keys are PascalCase,
entry-level keys are camelCase.

**Top-level fields:**

| Field | Type | Description |
|---|---|---|
| `Asks` | array | Ask (sell) orders, sorted by price ascending |
| `Bids` | array | Bid (buy) orders, sorted by price descending |
| `LastChange` | string | ISO 8601 timestamp of the last orderbook update |
| `SequenceNumber` | integer | Monotonically increasing sequence number |

**Each entry in `Asks` and `Bids`:**

| Field | Type | Description |
|---|---|---|
| `side` | string | `"sell"` for asks, `"buy"` for bids |
| `price` | string | Price level |
| `quantity` | string | Total quantity available at this price level (sum of all orders at this price) |
| `orderCount` | integer | Number of individual orders aggregated at this price level |
| `currencyPair` | string | Pair symbol, e.g. `"BTCUSDC"` |

`price` and `quantity` are strings. `orderCount` is an integer.

### Example response

```json
{
  "Asks": [
    {
      "side": "sell",
      "quantity": "0.09523556",
      "price": "67123",
      "currencyPair": "BTCUSDC",
      "orderCount": 1
    }
  ],
  "Bids": [
    {
      "side": "buy",
      "quantity": "0.07592137",
      "price": "67081",
      "currencyPair": "BTCUSDC",
      "orderCount": 2
    }
  ],
  "LastChange": "2026-03-08T17:31:26.406Z",
  "SequenceNumber": 1792329152
}
```

### Notes

- Returns up to 40 price levels per side.
- **Each price level aggregates multiple orders.** `quantity` is the total across all orders at that price; `orderCount` shows how many individual orders are behind it. Always note this when presenting an order book.
- `SequenceNumber` increases monotonically — useful for detecting missed updates when polling.
