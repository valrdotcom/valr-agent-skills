# Currencies Reference

> **Always call the API.** Do not answer from the examples in this file —
> call the endpoint via `valr_request.py` every time.

## Contents

- [Supported Currencies](#supported-currencies) — list all currencies, check
  deposit/withdrawal availability, look up supported networks

## Supported Currencies

Retrieve all currencies supported by VALR, including network and
deposit/withdrawal availability information.

```
GET /v1/public/currencies
```

This is a public endpoint — no credentials required.

### Usage

```bash
python3 scripts/valr_request.py GET /v1/public/currencies
```

### Response

Returns an array of currency objects.

| Field | Type | Description |
|---|---|---|
| `symbol` | string | Currency symbol, e.g. `"BTC"`, `"ETH"`. Note: `symbol` may differ from `shortName` for some currencies — always use `shortName` as the human-readable identifier. |
| `isActive` | boolean | Whether the currency is active on VALR |
| `shortName` | string | Short display name, e.g. `"BTC"`, `"ETH"` |
| `longName` | string | Full display name, e.g. `"Bitcoin"`, `"Ethereum"` |
| `decimalPlaces` | string | Number of decimal places for the currency |
| `withdrawalDecimalPlaces` | string | Maximum decimal places for withdrawals |
| `paymentReferenceFieldName` | string | Name of the memo/reference field for currencies that require one (e.g. XRP, XLM). Absent if not applicable. |
| `collateral` | boolean | Whether the currency can be used as loan collateral |
| `collateralWeight` | string | Collateral weight applied when used as collateral |
| `defaultNetworkType` | string | Default network used when none is specified on a deposit or withdrawal request. Absent if the currency has no networks. |
| `supportedNetworks` | array | Networks available for deposits and/or withdrawals. Absent if neither deposits nor withdrawals are available for this currency on VALR. |

Each entry in `supportedNetworks`:

| Field | Type | Description |
|---|---|---|
| `networkType` | string | Network identifier, e.g. `"Bitcoin"`, `"Ethereum"` |
| `networkLongName` | string | Human-readable network name |
| `minimumWithdrawAmount` | string | Minimum withdrawal amount on this network |
| `estimatedSendCost` | string | Estimated on-chain withdrawal fee |
| `deposit` | boolean | Whether deposits are available on this network |
| `withdraw` | boolean | Whether withdrawals are available on this network |
| `withdrawalDecimalPlaces` | string | Maximum decimal places accepted for withdrawals on this network |

### Example Response

```json
[
  {
    "symbol": "BTC",
    "isActive": true,
    "shortName": "BTC",
    "longName": "Bitcoin",
    "decimalPlaces": "8",
    "withdrawalDecimalPlaces": "8",
    "collateral": true,
    "collateralWeight": "0.95",
    "defaultNetworkType": "Bitcoin",
    "supportedNetworks": [
      {
        "networkType": "Bitcoin",
        "networkLongName": "Bitcoin",
        "minimumWithdrawAmount": "0.0002",
        "estimatedSendCost": "0.000012",
        "deposit": true,
        "withdraw": true,
        "withdrawalDecimalPlaces": "8"
      }
    ]
  }
]
```

### Notes

- If `supportedNetworks` is absent, deposits and withdrawals are not available for that currency on VALR.
- If `supportedNetworks` is present, check `deposit` and `withdraw` booleans on each network — one may be available without the other.
- `symbol` may differ from `shortName` — always use `shortName` as the human-readable identifier.
