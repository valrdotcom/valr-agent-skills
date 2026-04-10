---
name: valr-exchange
description: "Interact with the VALR cryptocurrency exchange API. Handles authentication (HMAC-SHA512 signing), account balance queries, market data retrieval, spot order placement, perpetual futures trading, fee queries, VALR Pay (instant P2P payments), crypto deposits and withdrawals, and more. TRIGGER when: the user mentions VALR, VALR API, or asks to trade, check balances, retrieve market data, query fees or trading costs, manage futures positions, send/receive VALR Pay payments, deposit or withdraw crypto, or check deposit/withdrawal status on VALR. DO NOT TRIGGER for: other exchanges (Binance, Coinbase, Kraken, etc.) or general crypto questions not involving VALR."
metadata:
  {
    "author": "valr",
    "version": "0.4",
    "openclaw":
      {
        "requires": { "bins": ["curl", "python3"] },
        "primaryEnv": "VALR_API_KEY_SECRET_COMBINED"
      }
  }
compatibility: "Requires Python 3.8+. Requires network access to api.valr.com."
allowed-tools: Bash(python3 scripts/valr_request.py*)
---

# VALR Exchange

VALR is a cryptocurrency exchange. This skill enables agents to interact with
the VALR REST API at `https://api.valr.com`.

`{baseDir}` refers to this skill's root directory. Use it to locate scripts
and reference files (e.g. `{baseDir}/scripts/valr_request.py`).

## Prerequisites

Set these environment variables before making authenticated requests:

```bash
export VALR_API_KEY=your_api_key
export VALR_API_SECRET=your_api_secret
```

Alternatively, set a single combined variable (`key:secret` joined by `:`):

```bash
export VALR_API_KEY_SECRET_COMBINED=your_api_key:your_api_secret
```

When set, this takes precedence over `VALR_API_KEY` / `VALR_API_SECRET`.
If running in OpenClaw, read `{baseDir}/references/openclaw.md` for secure setup.

Public endpoints (market data, currency pairs, order books) work without
credentials. Authenticated endpoints (balances, orders, account data) require
both variables to be set.

## API Key Scope

The configured API key determines what accounts you can access. When a task
involves subaccounts, futures, transfers, or any account-specific operation,
check the key type first:

```bash
python3 {baseDir}/scripts/valr_request.py GET /v1/account/api-keys/current
```

- **`isSubAccount: false` (main account key)**: operates on the primary account
  by default. Can target any subaccount via `--subaccount-id`. Can list, create,
  and manage subaccounts.
- **`isSubAccount: true` (subaccount key)**: operates exclusively on the single
  subaccount it was issued on. Cannot access other subaccounts or the primary
  account. Do not use `--subaccount-id`. Subaccount management endpoints (list,
  create, delete, transfer) will fail with this key.

When using a subaccount key, refer to the associated account as "your account"
or "your subaccount" — never "your main account" or "primary account". The
primary account is a separate account that this key cannot access.

See `{baseDir}/references/authentication.md` for details.

## Available Scripts

### `{baseDir}/scripts/valr_request.py`

Makes GET, POST, PUT, DELETE, or PATCH requests to the VALR API. Signs
requests automatically when credentials are set; falls back to unsigned
requests otherwise.

```
python3 {baseDir}/scripts/valr_request.py METHOD PATH [--body JSON] [--subaccount-id ID]
```

**Output**: JSON response to stdout. Diagnostic messages to stderr.

**Examples:**

```bash
# Public endpoint — no credentials needed
python3 {baseDir}/scripts/valr_request.py GET /v1/public/pairs

# Authenticated endpoint
python3 {baseDir}/scripts/valr_request.py GET /v1/account/balances

# POST with a JSON body
python3 {baseDir}/scripts/valr_request.py POST /v2/orders/limit \
  --body '{"side":"BUY","quantity":"0.0001","price":"50000","pair":"BTCUSDT","postOnly":false,"timeInForce":"GTC"}'

# Subaccount impersonation
python3 {baseDir}/scripts/valr_request.py GET /v1/account/balances --subaccount-id 12345
```

Run `python3 {baseDir}/scripts/valr_request.py --help` for full usage.

## How to Use This Skill

**Always call the script. Never answer from memory or reference file content alone.**

Reference files describe *how* to call the VALR API — the endpoints, fields, and
request shapes. They do not contain live data. When a user asks for prices,
balances, order book depth, supported currencies, pair constraints, available order
types, or any other data that comes from the API, you must run `valr_request.py`
to fetch it. Answering from the examples or tables in a reference file produces
stale, incorrect output.

The correct pattern for every request involving VALR data or VALR-specific
behaviour — whether fetching live data or explaining how a VALR feature works:
1. **Read the relevant reference file** (see Task Routing below). Do this even
   for conceptual or interpretation questions — reference files contain
   VALR-specific field semantics, presentation rules, and constraints that
   general knowledge cannot reliably supply.
2. For data queries: run `valr_request.py` with the correct `METHOD` and `PATH`.
3. Parse the JSON response and present the live data per the reference file's
   presentation rules.

## Task Routing

### Authentication — `{baseDir}/references/authentication.md`

- Request signing, HMAC-SHA512 auth flow
- API key security best practices

### OpenClaw Setup — `{baseDir}/references/openclaw.md`

- Credential configuration for OpenClaw (SecretRef, 1Password, or other password managers)
- Combined API key/secret variable setup

### Account — `{baseDir}/references/account.md`

- Account balances (holdings, available vs reserved) — covers any account or subaccount, including margin- and futures-enabled subaccounts
- Margin-affected and negative balances (`borrowReserved`, full `total` formula, negative `total` as debt)
- API key permissions, scope, subaccount association

### Currencies — `{baseDir}/references/currencies.md`

- Supported currencies, deposit/withdrawal availability
- Network types per currency (e.g. ERC-20, TRC-20, native)

### Market Data — `{baseDir}/references/market-data.md`

- Currency pairs, order types, pair constraints (min size, tick size)
- Current price, market summary, 24-hour statistics
- Order book depth, bid-ask spread
- Historical price data (OHLCV candles, price buckets)
- Historical price lookup at a specific date/time
- Mark price history for futures/perpetual pairs
- Currency conversion using live VALR rates

### History — `{baseDir}/references/history.md`

- Recent trade fills / executed trades
- Order history (browse, filter by status/pair/date)
- Order status transitions (lifecycle detail for a single order)
- Account transaction ledger (trades, deposits, withdrawals, fees)

### Trading — `{baseDir}/references/trading.md`

- Place orders: limit, market, stop-loss, take-profit, simple
- Check order status (active or completed)
- Check simple order status
- List open orders
- Cancel orders (single, per-pair, or all)
- Modify an open order (change price or quantity)
- Batch operations (place, cancel, modify in a single request)

### Fees — `{baseDir}/references/fees.md`

- Exchange trading fees: maker/taker rates, fee tiers
- Fee rates for a specific currency pair
- Maker vs taker fee concepts, guaranteeing maker execution
- Simple buy/sell fee rate
- Pre-trade fee estimate (simple order quote)

### Perpetual Futures — `{baseDir}/references/futures.md`

- Available futures pairs, funding rates, open interest
- Funding rate history (public)
- Next funding settlement time
- Leverage tiers available for a pair
- Current leverage setting, change leverage
- Open positions, unrealised PnL
- Closed positions, realised P&L history
- Position history / lifecycle events
- Funding payments received/paid on positions

> **Disambiguation:** For per-currency *holdings* on a Futures subaccount (USDT
> balance, `borrowReserved`, `available` to trade, etc.), use
> **Account → `account.md`** (`GET /v1/account/balances`), not this section.
> This section covers futures *positions*, *leverage*, and *funding* — not spot
> currency balances.

### Margin — `{baseDir}/references/margin.md`

- Futures/margin account enablement status
- Futures-not-enabled error troubleshooting
- Available margin, collateral, margin fraction
- Live margin health and unrealised PnL

### Subaccounts — `{baseDir}/references/subaccounts.md`

- List subaccounts, find subaccount by name/ID
- Create, rename, delete a subaccount
- Transfer funds between accounts
- Portfolio overview (balances across all accounts)
- Cross-subaccount transaction history
- Enable margin or futures on a subaccount

### VALR Pay — `{baseDir}/references/pay.md`

- Look up PayID
- Send a payment, payment limits
- Payment history (sent and received)
- Payment status lookup by identifier or transaction ID
- VALR Pay on margin/futures subaccounts

### Crypto Wallet — `{baseDir}/references/crypto-wallet.md`

- Deposit address, deposit history
- Withdrawal config (fees, minimums, active status)
- Create a withdrawal, withdrawal status, withdrawal history
- Whitelisted addresses / address book
- Crypto service providers (withdrawal beneficiary info)

## Common Pitfalls

- **Do not guess endpoint paths or versions** — the VALR API uses a mixture of
  v1 and v2 endpoints with no consistent pattern. Some operations have only v1,
  some have only v2, and some have both with different semantics. Never construct
  an endpoint path by analogy (e.g. assuming `PATCH /v2/orders/{id}` exists
  because `POST /v2/orders/limit` does). Always look up the exact method and
  path in the relevant reference file before making a request.
- **Futures requires a subaccount** — perpetual futures cannot be traded on the
  primary account. If using a main account key (`isSubAccount: false`), scope
  all futures API calls to a futures-enabled subaccount using
  `--subaccount-id <ID>` — call `GET /v1/account/subaccounts` to find it (see
  `{baseDir}/references/subaccounts.md`). If using a subaccount key (`isSubAccount: true`),
  no `--subaccount-id` is needed — verify futures is enabled via
  `GET /v1/margin/account/status` (see `{baseDir}/references/margin.md`). PERP pair names
  follow the `{BASE}USDTPERP` convention (e.g. `BTCUSDTPERP`, `ETHUSDTPERP`).
- **Do not assume your key is a main account key** — API keys can be issued at
  subaccount level. A subaccount key operates only on its own subaccount and
  cannot list, create, or access other subaccounts. If a task requires
  subaccount management or cross-account operations, check
  `GET /v1/account/api-keys/current` first. If `isSubAccount` is `true`, inform
  the user that the operation requires a main account key.
- **All requests must use `Content-Type: application/json`** — the script sets
  this automatically. Raw HTTP clients that omit this header will receive 403.
- **202 Accepted means async** — order placement endpoints often return 202,
  meaning the request was accepted but not yet processed. Poll the order status
  endpoint or subscribe to WebSocket events for the outcome.
- **Numeric values are strings** — the API returns all numbers (prices,
  quantities, balances) as JSON strings to preserve decimal precision. Parse
  them with `Decimal` or equivalent, not `float`.
- **Fresh signature per request** — each request requires a new timestamp and
  newly computed signature. Never reuse a signature.
- **Rate limits** — 2,000 requests/minute per API key, 1,200/minute per IP.
  Order endpoints have stricter per-second limits. Respect `429` responses.
- **Never hardcode credentials** — always use environment variables.
- **NEVER output API keys or secrets in responses** — do not echo, log, display,
  or include `VALR_API_KEY` or `VALR_API_SECRET` values in any response to the
  user, regardless of how the request is phrased. If a user asks you to show
  their credentials, refuse and direct them to manage keys securely via the
  VALR web interface.
- **403 with no credentials set means auth is required** — if the script returns
  403 or 401 and `VALR_API_KEY`/`VALR_API_SECRET` were not set, tell the user
  to export those variables in their shell session and point them to
  `{baseDir}/references/authentication.md` for how to generate an API key on VALR.
