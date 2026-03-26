# Margin

Margin is the collateral required to open and maintain leveraged positions.
On VALR, margin is fundamental to perpetual futures trading — every futures
position is a margin position.

## Contents

| What you need | Section | Key endpoint |
|---|---|---|
| Understand margin fractions and leverage | Key Concepts | — |
| Check whether margin/futures is enabled | Account Enablement | `GET /v1/margin/account/status` |
| Live margin health, collateral, and PnL | Live Margin Metrics | `GET /v2/margin/status` |
| View or change leverage for a pair | Leverage Management | *(see `references/futures.md`)* |

## Key Concepts

**Margin fraction** — the ratio of collateral to total position exposure. A
higher fraction means the account is better collateralised relative to its
positions. For example, a margin fraction of 0.5 means 50 cents of collateral
per dollar of exposure.

**Initial margin fraction** — the minimum collateral fraction required to open
a new position. Determined by the leverage tier selected for the pair
(e.g. 10x leverage → initial margin fraction of 0.1).

**Maintenance margin fraction** — the minimum fraction required to keep a
position open. Falling below this triggers liquidation.

**Auto-close margin fraction** — the fraction at which VALR begins liquidating
the position. This is set below the maintenance margin fraction to allow
gradual unwinding before full liquidation.

**Leverage multiple** — shorthand for `1 / initialMarginFraction`. At 10x
leverage, 10% margin is required to control 100% of the position value.

**Reference currency** — the currency in which margin metrics are expressed
(typically USDC or USDT depending on the account).

## Account Enablement

`GET /v1/margin/account/status` — returns whether margin and futures trading
are enabled on the account, and whether the account is in liquidation.

```bash
# Check the primary account (no --subaccount-id):
python3 scripts/valr_request.py GET /v1/margin/account/status

# Check a specific subaccount:
python3 scripts/valr_request.py GET /v1/margin/account/status \
  --subaccount-id YOUR_SUBACCOUNT_ID
```

When the user asks "is futures enabled?" without specifying a subaccount,
check the primary account first (without `--subaccount-id`).

**Response:**

```json
{
  "futuresEnabled": true,
  "marginEnabled": false,
  "inLiquidation": false
}
```

| Field | Type | Description |
|---|---|---|
| `futuresEnabled` | boolean | Whether perpetual futures trading is enabled on this subaccount |
| `marginEnabled` | boolean | Whether spot margin / borrow is enabled — independent of futures |
| `inLiquidation` | boolean | Whether the account is currently being liquidated; if `true`, new positions cannot be opened |

`futuresEnabled` and `marginEnabled` are independent flags. A subaccount can
have one, both, or neither enabled. Enablement is one-way and irreversible —
once enabled on a subaccount it cannot be undone, and the subaccount cannot be
deleted while either is enabled. Enablement can be done via the API using
`PUT /v1/margin/account/status` — see `references/subaccounts.md` for the
complete workflow.

### If futuresEnabled is false on the primary account

When checking the primary account and finding `futuresEnabled: false`, explain
that:

1. The primary account never has futures enabled — this is expected behaviour.
2. Futures trading requires a dedicated **subaccount** with futures explicitly
   enabled.
3. Futures can be enabled on a subaccount via the API using
   `PUT /v1/margin/account/status` — do not direct the user to the VALR website;
   show them the API path. See `references/subaccounts.md` for the full workflow.

> **Do not tell the user to use the VALR website to enable futures.** The API
> supports it directly via `PUT /v1/margin/account/status` scoped to a
> subaccount. Always present the API option.

**Note (main account keys):** Calling without `--subaccount-id` checks the
primary account, which always returns `futuresEnabled: false` and
`marginEnabled: false`. This is expected — the primary account cannot trade
futures or use margin. Always scope this call to the relevant subaccount.

### If futures is not enabled on a subaccount

Attempting to place a futures order on a subaccount without futures enabled
returns:

```json
{
  "code": -19227,
  "message": "Futures trading is not enabled for this account. Sign in to your account via website and navigate to a Futures pair to enable."
}
```

Ignore the "website" reference in the error message — futures can be enabled
via `PUT /v1/margin/account/status`. See `references/subaccounts.md` for the
complete workflow including how to find or create a suitable subaccount first.

## Live Margin Metrics

`GET /v2/margin/status` — returns the live margin state of the account:
current margin fraction, available margin, leverage in use, unrealised PnL,
and default margin fractions for the account.

```bash
python3 scripts/valr_request.py GET /v2/margin/status \
  --subaccount-id YOUR_SUBACCOUNT_ID
```

**Response:**

```json
{
  "marginFraction": "4898.27",
  "collateralizedMarginFraction": "0.575",
  "initialMarginFraction": "0.4997",
  "maintenanceMarginFraction": "0.2498",
  "autoCloseMarginFraction": "0.0083",
  "leverageMultiple": 0.01,
  "totalLeveragedExposureInReference": "6.94",
  "collateralizedBalancesInReference": "3.99",
  "referenceCurrency": "USDC",
  "initialRequiredInReference": "3.47",
  "availableInReference": "34003.74",
  "totalPositionsAtEntryInReference": "6.93",
  "totalUnrealisedFuturesPnlInReference": "-0.005",
  "totalBorrowedInReference": "0",
  "tradeReservedInReference": "0",
  "defaultInitialMarginFraction": "0.1",
  "defaultMaintenanceMarginFraction": "0.05",
  "defaultAutoCloseMarginFraction": "0.03"
}
```

| Field | Description |
|---|---|
| `marginFraction` | Overall margin health ratio; higher is safer |
| `collateralizedMarginFraction` | Fraction of exposure covered by collateralised balances |
| `initialMarginFraction` | Current blended initial margin fraction across all open positions |
| `maintenanceMarginFraction` | Current blended maintenance margin fraction; account is liquidated if margin falls below this |
| `autoCloseMarginFraction` | Level at which VALR begins closing positions |
| `leverageMultiple` | Current effective leverage across all open positions |
| `totalLeveragedExposureInReference` | Total notional value of open positions in reference currency |
| `collateralizedBalancesInReference` | Total collateral value in reference currency |
| `referenceCurrency` | Currency in which all values are expressed |
| `initialRequiredInReference` | Minimum collateral required to open current positions |
| `availableInReference` | Margin available to open new positions |
| `totalPositionsAtEntryInReference` | Total entry value of open positions |
| `totalUnrealisedFuturesPnlInReference` | Unrealised PnL across all open futures positions |
| `totalBorrowedInReference` | Total borrowed amount (spot margin) |
| `tradeReservedInReference` | Margin reserved for pending orders |
| `defaultInitialMarginFraction` | Default initial margin fraction for new positions (before leverage selection) |
| `defaultMaintenanceMarginFraction` | Default maintenance margin fraction |
| `defaultAutoCloseMarginFraction` | Default auto-close margin fraction |

All numeric values are returned as strings except `leverageMultiple` which is
a number.

## Leverage Management

To view or change the leverage tier for a specific futures pair, see the
**Leverage Configuration** section in `references/futures.md`. The relevant
endpoints are:

- `GET /v1/margin/leverage/{currencyPair}` — current leverage and margin fractions
- `PUT /v1/margin/leverage/{currencyPair}` — change the leverage tier
