---
name: valr-exchange
description: "Interact with the VALR cryptocurrency exchange API. Handles authentication (HMAC-SHA512 signing), account balance queries, market data retrieval, spot order placement, perpetual futures trading, fee queries, VALR Pay (instant P2P payments), crypto deposits and withdrawals, and more. TRIGGER when: the user mentions VALR, VALR API, or asks to trade, check balances, retrieve market data, query fees or trading costs, manage futures positions, send/receive VALR Pay payments, deposit or withdraw crypto, or check deposit/withdrawal status on VALR. DO NOT TRIGGER for: other exchanges (Binance, Coinbase, Kraken, etc.) or general crypto questions not involving VALR."
metadata:
  author: valr
  version: "0.2"
compatibility: "Requires Python 3.8+. Requires network access to api.valr.com."
allowed-tools: Bash(python3 scripts/valr_request.py*)
---

# VALR Exchange

VALR is a cryptocurrency exchange. This skill enables agents to interact with
the VALR REST API at `https://api.valr.com`.

## Prerequisites

Set these environment variables before making authenticated requests:

```bash
export VALR_API_KEY=your_api_key
export VALR_API_SECRET=your_api_secret
```

Public endpoints (market data, currency pairs, order books) work without
credentials. Authenticated endpoints (balances, orders, account data) require
both variables to be set.

## Available Scripts

### `scripts/valr_request.py`

Makes GET, POST, PUT, DELETE, or PATCH requests to the VALR API. Signs
requests automatically when credentials are set; falls back to unsigned
requests otherwise.

```
python3 scripts/valr_request.py METHOD PATH [--body JSON] [--subaccount-id ID]
```

**Output**: JSON response to stdout. Diagnostic messages to stderr.

**Examples:**

```bash
# Public endpoint — no credentials needed
python3 scripts/valr_request.py GET /v1/public/pairs

# Authenticated endpoint
python3 scripts/valr_request.py GET /v1/account/balances

# POST with a JSON body
python3 scripts/valr_request.py POST /v2/orders/limit \
  --body '{"side":"BUY","quantity":"0.0001","price":"50000","pair":"BTCUSDT","postOnly":false,"timeInForce":"GTC"}'

# Subaccount impersonation
python3 scripts/valr_request.py GET /v1/account/balances --subaccount-id 12345
```

Run `python3 scripts/valr_request.py --help` for full usage.

## How to Use This Skill

**Always call the script. Never answer from memory or reference file content alone.**

Reference files describe *how* to call the VALR API — the endpoints, fields, and
request shapes. They do not contain live data. When a user asks for prices,
balances, order book depth, supported currencies, pair constraints, available order
types, or any other data that comes from the API, you must run `valr_request.py`
to fetch it. Answering from the examples or tables in a reference file produces
stale, incorrect output.

The correct pattern for every data request:
1. **Read the relevant reference file** (see Task Routing below). Do this even
   if you already know the endpoint — reference files contain required
   **presentation rules** (e.g. how to display balances, ordering conventions,
   mandatory callouts) that you must follow when responding to the user.
2. Run `valr_request.py` with the correct `METHOD` and `PATH`.
3. Parse the JSON response and present the live data per the reference file's
   presentation rules.

## Task Routing

| Task | Reference file to read |
|---|---|
| How does authentication / request signing work? | `references/authentication.md` |
| How does API key security work? / API key security best practices | `references/authentication.md` |
| Check account balances | `references/account.md` |
| Check what permissions / capabilities the current API key has | `references/account.md` |
| What currencies does VALR support? | `references/currencies.md` |
| What networks are available for a currency (deposit/withdrawal networks)? | `references/currencies.md` |
| What can I trade on VALR? / What markets are available? | `references/market-data.md` |
| What currency pairs can I trade on VALR? | `references/market-data.md` |
| What are the order size limits or tick size for a pair? | `references/market-data.md` |
| What order types does VALR support? | `references/market-data.md` |
| What order types are available for a specific pair? | `references/market-data.md` |
| What is the current price of a currency? (e.g. what is BTC trading at?) | `references/market-data.md` |
| Show market overview / 24-hour statistics | `references/market-data.md` |
| Show the order book / bid-ask spread for a currency pair | `references/market-data.md` |
| Get historical price data / OHLCV / candle data for a pair | `references/market-data.md` |
| What was the price at a specific date or time? (past/historical price lookup) | `references/market-data.md` |
| Get mark price history for a futures/perpetual pair | `references/market-data.md` |
| Convert an amount from one currency to another using VALR rates | `references/market-data.md` |
| Aggregate trade values across pairs with different quote currencies | `references/market-data.md` |
| View recent trade fills / executed trades | `references/history.md` |
| Browse past orders / order history | `references/history.md` |
| Filter order history by status, pair, or date | `references/history.md` |
| See all status transitions for a specific order | `references/history.md` |
| View account transaction history / ledger | `references/history.md` |
| Place a limit order | `references/trading.md` |
| Place a market order | `references/trading.md` |
| Place a stop-loss or take-profit order | `references/trading.md` |
| Place a simple order | `references/trading.md` |
| Check the status of a simple order | `references/trading.md` |
| List open orders | `references/trading.md` |
| Check the status of an order | `references/trading.md` |
| Cancel all open orders (all pairs) | `references/trading.md` |
| Cancel all open orders for a specific pair | `references/trading.md` |
| Cancel an order | `references/trading.md` |
| Modify an open order / change order price or quantity | `references/trading.md` |
| Place multiple orders in a single request / batch orders | `references/trading.md` |
| Place, cancel, or modify multiple orders at once | `references/trading.md` |
| What is my simple buy/sell fee rate? | `references/fees.md` |
| Get a fee estimate before placing a simple order | `references/fees.md` |
| What are my exchange trading fees / fee rates? | `references/fees.md` |
| What is the difference between maker and taker fees? | `references/fees.md` |
| What are my fees for a specific currency pair? | `references/fees.md` |
| How do I guarantee I pay maker fees on an order? | `references/fees.md` |
| What fee tier am I on? / How are my fees calculated? | `references/fees.md` |
| What leverage tiers are available for a futures pair? | `references/futures.md` |
| What perpetual futures pairs does VALR offer? | `references/futures.md` |
| What is the current funding rate for a futures pair? | `references/futures.md` |
| What is the open interest for a futures pair? | `references/futures.md` |
| When is the next funding settlement? | `references/futures.md` |
| Show funding rate history for a futures pair (public data, no auth needed) | `references/futures.md` |
| What leverage am I using on a futures pair? | `references/futures.md` |
| Set / change leverage for a futures pair | `references/futures.md` |
| Show my open futures positions / what futures positions do I have? | `references/futures.md` |
| What is my unrealised PnL on futures? | `references/futures.md` |
| Show my closed futures positions / futures P&L history | `references/futures.md` |
| Show position history / lifecycle for a futures pair | `references/futures.md` |
| Show my funding payments on futures positions (authenticated, per-account) | `references/futures.md` |
| Is futures / perpetual futures trading enabled on my account or subaccount? | `references/margin.md` |
| How much margin / collateral do I have available? | `references/margin.md` |
| Is margin trading enabled on my account or subaccount? | `references/margin.md` |
| Why am I getting a futures-not-enabled error? | `references/margin.md` |
| What is my current margin status, available margin, or unrealised PnL? | `references/margin.md` |
| List my subaccounts / what subaccounts do I have? | `references/subaccounts.md` |
| What is my subaccount ID? / Find a subaccount by name | `references/subaccounts.md` |
| Create a subaccount | `references/subaccounts.md` |
| Rename or update a subaccount | `references/subaccounts.md` |
| Delete a subaccount | `references/subaccounts.md` |
| Transfer funds between subaccounts / internal transfer | `references/subaccounts.md` |
| View balances across all accounts / portfolio overview | `references/subaccounts.md` |
| Cross-subaccount transaction history | `references/subaccounts.md` |
| Enable margin or futures trading on a subaccount | `references/subaccounts.md` |
| What is my VALR PayID? / What is my Pay ID? | `references/pay.md` |
| Send a VALR Pay payment / pay someone on VALR | `references/pay.md` |
| What are the payment limits for VALR Pay? | `references/pay.md` |
| View VALR Pay payment history / payments sent or received | `references/pay.md` |
| Check the status of a VALR Pay payment | `references/pay.md` |
| Look up a VALR Pay payment by identifier or transaction ID | `references/pay.md` |
| Can I use VALR Pay on a margin or futures subaccount? | `references/pay.md` |
| Get my deposit address for a currency | `references/crypto-wallet.md` |
| View crypto deposit history (wallet-level) | `references/crypto-wallet.md` |
| Check withdrawal fees or minimum withdrawal amount | `references/crypto-wallet.md` |
| Withdraw crypto / send crypto to an external address | `references/crypto-wallet.md` |
| Check the status of a crypto withdrawal | `references/crypto-wallet.md` |
| View crypto withdrawal history (wallet-level) | `references/crypto-wallet.md` |
| View deposits and withdrawals in the transaction ledger | `references/history.md` |
| View whitelisted withdrawal addresses / address book | `references/crypto-wallet.md` |
| Look up crypto service providers for withdrawal beneficiary info | `references/crypto-wallet.md` |

## Common Pitfalls

- **Do not guess endpoint paths or versions** — the VALR API uses a mixture of
  v1 and v2 endpoints with no consistent pattern. Some operations have only v1,
  some have only v2, and some have both with different semantics. Never construct
  an endpoint path by analogy (e.g. assuming `PATCH /v2/orders/{id}` exists
  because `POST /v2/orders/limit` does). Always look up the exact method and
  path in the relevant reference file before making a request.
- **Futures requires a subaccount** — perpetual futures cannot be traded on the
  primary account. All futures API calls (positions, leverage, funding) must be
  scoped to a futures-enabled subaccount using `--subaccount-id <ID>`. To find
  the subaccount ID, call `GET /v1/account/subaccounts` first (see
  `references/subaccounts.md`). PERP pair names follow the `{BASE}USDTPERP`
  convention (e.g. `BTCUSDTPERP`, `ETHUSDTPERP`).
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
  `references/authentication.md` for how to generate an API key on VALR.
