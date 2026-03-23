# Crypto Wallet Reference

> **Always call the API.** Do not answer from the examples in this file —
> call the endpoint via `valr_request.py` every time.

## Permissions

- **View** — required for all read operations (deposit address, history,
  withdrawal config/status/history, address book, service providers)
- **Withdraw** — required to create withdrawals

## Quick Reference

> **Read the full section for any operation before calling the endpoint.**
> The table below is a routing aid — it does not show required fields,
> body schemas, or response formats.

| Operation | Endpoint | Key Detail |
|---|---|---|
| Get deposit address | `GET /v1/wallet/crypto/{currency}/deposit/address` | Optional `?networkType=` query param |
| View deposit history | `GET /v1/wallet/crypto/deposit/history` | Pagination: `skip`, `limit` (max 100) |
| Check withdrawal config | `GET /v1/wallet/crypto/{currency}/withdraw` | Returns fees, minimums, active status |
| Create a withdrawal | `POST /v1/wallet/crypto/{currency}/withdraw` | Body: amount + address or addressBookId |
| Check withdrawal status | `GET /v1/wallet/crypto/{currency}/withdraw/{id}` | Both currency and withdrawal ID in path |
| View withdrawal history | `GET /v1/wallet/crypto/withdraw/history` | Pagination: `skip`, `limit` (max 100) |
| List whitelisted addresses | `GET /v1/wallet/crypto/address-book` | All currencies |
| List whitelisted addresses (currency) | `GET /v1/wallet/crypto/address-book/{currency}` | Filtered to one currency |
| List service providers | `GET /v1/wallet/crypto/service-providers` | For beneficiary info on withdrawals |
| Unified transaction ledger (deposits, withdrawals, trades, etc.) | See `references/history.md` | `GET /v1/account/transactionhistory` with `transactionTypes` filter |

---

## Get Deposit Address

`GET /v1/wallet/crypto/{currency}/deposit/address`

Returns the deposit address for the specified currency.

| Parameter | In | Required | Notes |
|---|---|---|---|
| `currency` | path | Yes | Currency code, e.g. `BTC`, `ETH`, `XRP` |
| `networkType` | query | No | Network to use. Defaults to the currency's `defaultNetworkType` from `references/currencies.md`. |

### Response (`200 OK`)

```json
{
  "currency": "BTC",
  "address": "2Mw7EDz9nj48LkwD8YzAogF6qm7VD562hd6",
  "networkType": "Bitcoin"
}
```

| Field | Type | Description |
|---|---|---|
| `currency` | string | Currency code |
| `address` | string | Deposit address |
| `networkType` | string | Network for this address |

To check which networks a currency supports for deposits, see
`references/currencies.md` — look at the `supportedNetworks` array and the
`deposit` boolean on each network.

---

## Deposit History

`GET /v1/wallet/crypto/deposit/history`

Returns deposit history records, optionally filtered by currency and date range.

| Parameter | In | Required | Notes |
|---|---|---|---|
| `currency` | query | No | Filter by currency code. Omit for all currencies. |
| `skip` | query | No | Number of results to skip. Default `0`. |
| `limit` | query | No | Max results to return. Default and max `100`. |
| `startTime` | query | No | ISO 8601 datetime, e.g. `2025-01-01T00:00:00Z`. Returns deposits since this time. |
| `endTime` | query | No | ISO 8601 datetime. Returns deposits up to and including this time. |

### Response (`200 OK`)

```json
[
  {
    "currencyCode": "ETH",
    "receiveAddress": "0xa47156dab9c66881f8d860a53133e229337e95bd",
    "transactionHash": "0x02f971fad308c5c9532d5ae19e657f31dbb63d46d42dc5561b44ad5818209217",
    "amount": "0.01",
    "createdAt": "2023-12-01T13:36:36Z",
    "confirmations": 5,
    "confirmed": true,
    "confirmedAt": "2023-12-01T13:37:44.951759Z"
  }
]
```

| Field | Type | Description |
|---|---|---|
| `currencyCode` | string | Currency code |
| `receiveAddress` | string | Address that received the deposit |
| `transactionHash` | string | On-chain transaction hash |
| `amount` | string | Deposited amount |
| `createdAt` | string | ISO 8601 timestamp when the deposit was detected |
| `confirmations` | integer | Number of on-chain confirmations |
| `confirmed` | boolean | Whether the deposit has been confirmed and credited |
| `confirmedAt` | string | ISO 8601 timestamp when the deposit was confirmed |

For a unified ledger view of all transaction types including deposits, use
`GET /v1/account/transactionhistory` with `transactionTypes=BLOCKCHAIN_RECEIVE` —
see `references/history.md`.

---

## Withdrawal Config Info

`GET /v1/wallet/crypto/{currency}/withdraw`

Returns withdrawal configuration for a currency: fees, minimum amounts, whether
withdrawals are currently active. **Always check this before creating a
withdrawal.**

| Parameter | In | Required | Notes |
|---|---|---|---|
| `currency` | path | Yes | Currency code, e.g. `BTC`, `ETH` |
| `networkType` | query | No | Network to query config for. Defaults to the currency's `defaultNetworkType`. |

### Response (`200 OK`)

```json
{
  "currency": "BTC",
  "minimumWithdrawAmount": "0.00004422",
  "withdrawalDecimalPlaces": "8",
  "isActive": true,
  "withdrawCost": "0.000011",
  "networkType": "Bitcoin",
  "supportsPaymentReference": false
}
```

| Field | Type | Description |
|---|---|---|
| `currency` | string | Currency code |
| `minimumWithdrawAmount` | string | Minimum amount that can be withdrawn |
| `withdrawalDecimalPlaces` | string | Max decimal places accepted for the withdrawal amount |
| `isActive` | boolean | Whether withdrawals are currently enabled for this currency/network |
| `withdrawCost` | string | On-chain fee deducted from the withdrawal |
| `networkType` | string | Network this config applies to |
| `supportsPaymentReference` | boolean | Whether a memo/reference can be attached (e.g. for XRP, XLM) |

### Notes

- `withdrawCost` is deducted from the withdrawn amount — the recipient receives
  `amount - withdrawCost`.
- If `isActive` is `false`, withdrawal requests for this currency/network will
  be rejected.
- Amounts with more decimal places than `withdrawalDecimalPlaces` are rounded
  down silently.

---

## Create a Crypto Withdrawal

`POST /v1/wallet/crypto/{currency}/withdraw`

Submits a withdrawal request. Returns `202 Accepted` — the withdrawal is queued
for processing asynchronously. Use the returned `id` with the withdrawal status
endpoint to track progress.

> **On-chain withdrawals are irreversible once confirmed.** Sending to the wrong
> address or on the wrong network can result in permanent loss of funds.

### Before withdrawing

1. **Check withdrawal config** — call `GET /v1/wallet/crypto/{currency}/withdraw`
   to verify `isActive` is `true` and the amount meets `minimumWithdrawAmount`.
2. **Check your balance** — call `GET /v1/account/balances` (see
   `references/account.md`) to confirm sufficient `available` balance.
3. **Verify the network** — if specifying `networkType`, ensure it matches the
   destination address. Mismatched network and address can cause loss of funds.
   To look up supported networks for a currency, see `references/currencies.md`.

### Request

| Parameter | In | Required | Notes |
|---|---|---|---|
| `currency` | path | Yes | Currency code, e.g. `BTC`, `ETH` |

**Request body:**

```json
{
  "amount": "0.001",
  "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
  "networkType": "Bitcoin"
}
```

| Field | Required | Notes |
|---|---|---|
| `amount` | Yes | Amount to withdraw, as a string |
| `address` | Conditional | Destination address. Provide `address` **or** `addressBookId`, not both. |
| `addressBookId` | Conditional | UUID of a whitelisted address book entry. Provide `addressBookId` **or** `address`, not both. When using `addressBookId`, `networkType` is taken from the address book entry. |
| `networkType` | No | Network to use. Defaults to currency's `defaultNetworkType`. **Must match the destination address.** |
| `paymentReference` | No | Memo or reference for currencies that support it (e.g. XRP, XLM). Max 256 characters. Check `supportsPaymentReference` in withdrawal config. |
| `beneficiaryName` | Conditional | Full name of the recipient. Required for accounts subject to regulatory requirements, unless an `addressBookId` with saved beneficiary info is provided. |
| `isCorporate` | Conditional | `true` if the recipient is a legal entity, `false` if a person. |
| `isSelfHosted` | Conditional | `true` if the recipient controls their own keys, `false` if they use a service provider. |
| `serviceProviderId` | Conditional | UUID of the recipient's service provider (from `GET /v1/wallet/crypto/service-providers`). Use when `isSelfHosted` is `false`. Cannot be combined with `serviceProviderName`. |
| `serviceProviderName` | Conditional | Name of the recipient's service provider, when the provider is not in the service providers list. Cannot be combined with `serviceProviderId`. |
| `allowBorrow` | No | If `true`, borrow funds against account assets to cover the withdrawal. Default `false`. Only available in margin-enabled subaccounts. |

### Using an address book entry

When withdrawing via `addressBookId`, the network type and beneficiary
information are taken from the saved address book entry. This is the safest
approach — it avoids network mismatch risk and ensures beneficiary fields are
pre-populated.

Address book entries can only be created through the VALR website — there is no
API endpoint for creating them. Use `GET /v1/wallet/crypto/address-book` to list
existing entries and obtain their IDs.

### Response (`202 Accepted`)

```json
{
  "id": "686ce4b8-1504-4f9c-b217-f6f24300cfb3"
}
```

The `id` is the withdrawal request UUID. Use it with
`GET /v1/wallet/crypto/{currency}/withdraw/{id}` to check status.

---

## Check Withdrawal Status

`GET /v1/wallet/crypto/{currency}/withdraw/{id}`

Returns the current status of a withdrawal.

| Parameter | In | Required | Notes |
|---|---|---|---|
| `currency` | path | Yes | Currency code for the withdrawal |
| `id` | path | Yes | Withdrawal UUID returned by `POST .../withdraw` |

### Response (`200 OK`)

```json
{
  "currency": "BTC",
  "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
  "amount": "0.001",
  "feeAmount": "0.000011",
  "transactionHash": "a1b2c3d4e5f6...",
  "confirmations": 2,
  "lastConfirmationAt": "2025-01-07T14:22:32.419194",
  "uniqueId": "686ce4b8-1504-4f9c-b217-f6f24300cfb3",
  "createdAt": "2025-01-07T14:19:17.861765Z",
  "verified": true,
  "status": "Processing",
  "networkType": "Bitcoin"
}
```

| Field | Type | Description |
|---|---|---|
| `currency` | string | Currency code |
| `address` | string | Destination address |
| `amount` | string | Withdrawal amount |
| `feeAmount` | string | On-chain fee charged |
| `transactionHash` | string | On-chain transaction hash (populated once broadcast) |
| `confirmations` | integer | Number of on-chain confirmations |
| `lastConfirmationAt` | string | Timestamp of the most recent confirmation |
| `uniqueId` | string | Withdrawal UUID |
| `createdAt` | string | ISO 8601 timestamp when the withdrawal was created |
| `verified` | boolean | Whether the withdrawal has been verified |
| `status` | string | Withdrawal status, e.g. `"Processing"`, `"Complete"` |
| `networkType` | string | Network used for the withdrawal |

If the withdrawal ID is not found, the API returns error code `-13403` with
message `"Could not find send"`.

---

## Withdrawal History

`GET /v1/wallet/crypto/withdraw/history`

Returns withdrawal history records, optionally filtered by currency and date
range.

| Parameter | In | Required | Notes |
|---|---|---|---|
| `currency` | query | No | Filter by currency code. Omit for all currencies. |
| `skip` | query | No | Number of results to skip. Default `0`. |
| `limit` | query | No | Max results to return. Default and max `100`. |
| `startTime` | query | No | ISO 8601 datetime. Returns withdrawals since this time. |
| `endTime` | query | No | ISO 8601 datetime. Returns withdrawals up to and including this time. |

### Response (`200 OK`)

Returns an array of withdrawal records with the same fields as the withdrawal
status response (see [Check Withdrawal Status](#check-withdrawal-status)).

For a unified ledger view of all transaction types including withdrawals, use
`GET /v1/account/transactionhistory` with `transactionTypes=BLOCKCHAIN_SEND` —
see `references/history.md`.

---

## Address Book

Retrieve whitelisted withdrawal addresses. Address book entries can only be
created through the VALR website — there is no API endpoint for creating them.

### All currencies

`GET /v1/wallet/crypto/address-book`

Returns all whitelisted withdrawal addresses across all currencies.

### Single currency

`GET /v1/wallet/crypto/address-book/{currency}`

| Parameter | In | Required | Notes |
|---|---|---|---|
| `currency` | path | Yes | Currency code, e.g. `BTC`, `ETH` |

### Response (`200 OK`)

Both endpoints return the same response shape:

```json
[
  {
    "id": "2a22433a-1548-11eb-adc1-0242ac120002",
    "label": "My BTC Wallet",
    "currency": "BTC",
    "address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
    "networkType": "Bitcoin",
    "createdAt": "2024-11-30T10:18:54.994930Z",
    "beneficiaryName": "Jane Doe",
    "isCorporate": false,
    "isSelfHosted": false,
    "serviceProviderName": "Binance"
  }
]
```

| Field | Type | Description |
|---|---|---|
| `id` | string | UUID of the address book entry — use as `addressBookId` when withdrawing |
| `label` | string | User-defined label |
| `currency` | string | Currency code |
| `address` | string | Whitelisted withdrawal address |
| `networkType` | string | Network type for this address |
| `createdAt` | string | ISO 8601 timestamp when the entry was created |
| `beneficiaryName` | string | Name of the beneficiary (if saved) |
| `isCorporate` | boolean | Whether the beneficiary is a legal entity |
| `isSelfHosted` | boolean | Whether the address is self-hosted (recipient controls own keys) |
| `serviceProviderName` | string | Service provider name (present when `isSelfHosted` is `false`) |

---

## Service Providers

`GET /v1/wallet/crypto/service-providers`

Returns the list of known crypto service providers. Use the `id` from this list
as `serviceProviderId` when creating withdrawals where the recipient uses a
service provider.

### Response (`200 OK`)

```json
[
  {
    "id": "672b1ff8a1ff8a027906ff39",
    "name": "Bybit"
  },
  {
    "id": "676d1c189ef2fd542e5bbf33",
    "name": "Binance"
  }
]
```

| Field | Type | Description |
|---|---|---|
| `id` | string | Service provider identifier — use as `serviceProviderId` in withdrawal requests |
| `name` | string | Service provider name |
