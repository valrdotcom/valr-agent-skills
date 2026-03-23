# VALR Pay Reference

> **Always call the API.** Do not answer from the examples in this file —
> call the endpoint via `valr_request.py` every time.

## What is VALR Pay?

VALR Pay is an instant peer-to-peer payment feature that lets VALR users send
and receive funds without blockchain transactions or wallet addresses. Payments
settle immediately between VALR accounts.

Recipients are identified by one of three methods:
- **PayID** — a unique 20-character alphanumeric code tied to a VALR account
  (e.g. `ZJ9UX4LBBTRAXD2W7Z5V`)
- **Email address** — the email registered on the recipient's VALR account
- **Cell phone number** — the mobile number registered on the recipient's account

Payments can be anonymous (sender identity hidden from recipient), and both
parties can attach notes. VALR Pay supports multiple currencies including USDT,
BTC, and ZAR.

> **Always fetch live data.** Do not answer VALR Pay questions from the examples
> or tables in this file — call the API via `valr_request.py` every time. The
> examples here illustrate response shape only.

## Permissions

- **View** — required for all read endpoints (PayID, limits, history, lookup)
- **Internal Transfer** — required to send payments (`POST /v1/pay`)

## Contents

| Operation | Section | Endpoint |
|---|---|---|
| Get your PayID | Get Your PayID | `GET /v1/pay/payid` |
| Check payment limits for a currency | Get Payment Limits | `GET /v1/pay/limits?currency={currency}` |
| Send a payment | Send a Payment | `POST /v1/pay` |
| List past payments | Payment History | `GET /v1/pay/history` |
| Look up a specific payment | Look Up a Payment | `GET /v1/pay/transactionid/{id}` |

> **Important:** VALR Pay is not available on margin- or futures-enabled
> subaccounts — see Margin / Futures Account Restriction below.

## Margin / Futures Account Restriction

**VALR Pay is not available on subaccounts with margin trading enabled.**
Because futures trading implicitly requires margin, futures-enabled subaccounts
are also restricted. Attempting to use Pay endpoints that require account
context on such a subaccount returns:

```json
{"code": -15437, "message": "VALR Pay not supported on an account with margin trading enabled. Coming soon!"}
```

Use the **primary account** (no `X-VALR-SUB-ACCOUNT-ID` header) or a standard
subaccount without margin or futures enabled.

Note: `GET /v1/pay/limits` and `GET /v1/pay/history` do not return this error
on margin-enabled accounts (they return data normally), but the account cannot
actually send or receive payments.

---

## Get Your PayID

`GET /v1/pay/payid`

Returns the unique PayID for the current account. Share this with others so
they can send payments to you.

**Response:**

```json
{"payId": "ZJ9UX4LBBTRAXD2W7Z5V"}
```

The PayID is always exactly 20 characters, alphanumeric, uppercase.

---

## Get Payment Limits

`GET /v1/pay/limits?currency={currency}`

Returns the per-transaction minimum and maximum payment amounts for a given
currency. Limits vary by currency — always call this endpoint to get the
current values rather than using any example values from this file.

**Required query parameter:**

| Parameter | Description |
|---|---|
| `currency` | Currency code, e.g. `USDT`, `BTC`, `ZAR` |

**Response:**

```json
{
  "maxPaymentAmount": 10.00,
  "minPaymentAmount": 0.00015,
  "paymentCurrency": "BTC",
  "limitType": "per transaction"
}
```

`limitType` describes the scope of the limit (e.g. `"per transaction"`). If the
payment amount is below the minimum, the API returns error `-15430` with a
message stating the minimum.

---

## Send a Payment

`POST /v1/pay`

Initiates an instant payment to another VALR user. Returns **202 Accepted**
— the request is queued asynchronously. Use the returned `transactionId` to
poll for the final status.

**Before sending, you must check limits.** Call `GET /v1/pay/limits?currency={currency}`
first to confirm the amount meets the per-transaction minimum. If the amount is
below the minimum the API returns error `-15430`. Do not skip this step.

**Request body:**

```json
{
  "currency": "USDT",
  "amount": "5",
  "recipientPayId": "CGFQFFLT8832DWY74LD3",
  "senderNote": "Thanks for lunch",
  "recipientNote": "Enjoy!",
  "anonymous": false
}
```

| Field | Required | Notes |
|---|---|---|
| `currency` | Yes | Currency code (e.g. `"USDT"`, `"BTC"`, `"ZAR"`) |
| `amount` | Yes | Payment amount as a string |
| `recipientPayId` | Conditional | Recipient's PayID. Exactly **one** of `recipientPayId`, `recipientEmail`, or `recipientCellNumber` must be provided. |
| `recipientEmail` | Conditional | Recipient's registered VALR email address. |
| `recipientCellNumber` | Conditional | Recipient's registered VALR cell phone number. |
| `senderNote` | No | Note visible to the sender only |
| `recipientNote` | No | Note visible to the recipient only |
| `anonymous` | Yes | `true` hides your identity from the recipient. Default `false`. |

**202 response body:**

```json
{
  "identifier": "d2e16dc6-0c83-4f70-a30e-ef958a2b1d5d",
  "transactionId": "918486592856862720"
}
```

**After receiving 202, immediately poll for the final status.** Call
`GET /v1/pay/transactionid/{transactionId}` using the `transactionId` from the
202 response body and report the resulting `status` to the user. Do not leave
the user with just an identifier — confirm whether the payment completed.

**Common errors:**

| Code | Message | Cause |
|---|---|---|
| -15417 | Payment has too many recipient identifiers | More than one of recipientPayId / recipientEmail / recipientCellNumber provided |
| -15426 | Payment cannot be sent to yourself | Recipient resolves to the sender's own account |
| -15430 | Minimum payment amount is {N} {currency} | Amount is below the per-transaction minimum |
| -15437 | VALR Pay not supported on an account with margin trading enabled | Sending from a margin or futures-enabled subaccount |
| -15401 | Unable to make payment. Please contact support | Recipient not found, or other unrecoverable error |

---

## Payment History

`GET /v1/pay/history`

Returns a list of all payments sent from and received by the current account.

**Query parameters (all optional):**

| Parameter | Description |
|---|---|
| `status` | Comma-separated status filter. Valid values: `INITIATED`, `AUTHORISED`, `COMPLETE`, `RETURNED`, `FAILED`, `EXPIRED` |
| `skip` | Number of records to skip (pagination) |
| `limit` | Maximum number of records to return |

**Response** — array of payment objects:

```json
[
  {
    "identifier": "42e4c2ce-df12-4f77-81f6-661b4d226374",
    "otherPartyIdentifier": "Oz",
    "amount": 200,
    "currency": "ZAR",
    "status": "COMPLETE",
    "timestamp": "2022-04-29T09:46:51.132056Z",
    "note": "Test",
    "transactionId": "969534114340323328",
    "anonymous": false,
    "reversed": false,
    "type": "CREDIT"
  }
]
```

**Field notes:**

| Field | Notes |
|---|---|
| `type` | `"CREDIT"` = payment received; `"DEBIT"` = payment sent |
| `amount` | Numeric (not a string, unlike most VALR fields) |
| `status` | May be absent on some records; use `GET /v1/pay/transactionid/{id}` for a guaranteed status field |
| `note` | Single combined note field. The separate `senderNote` / `recipientNote` distinction in the send request does not appear in history — notes are surfaced as a single `note` field |
| `otherPartyIdentifier` | Display name or identifier of the other party; `anonymous` payments from others will show a generic identifier |
| `reversed` | `true` if a full or partial reversal has occurred |

**Presentation rules:** Always label `CREDIT` as "received" and `DEBIT` as
"sent". Show `currency`, `amount`, `type`, `status` (if present), `timestamp`,
and `note` (if present). Indicate if the payment has been reversed.

---

## Look Up a Payment

Two endpoints let you retrieve a specific payment. They return overlapping but
not identical schemas.

### By identifier (UUID)

`GET /v1/pay/identifier/{identifier}`

Returns the same schema as a history entry (see above). Use this when you have
the UUID from a history list or from the 202 response to a send.

### By transaction ID

`GET /v1/pay/transactionid/{transactionId}`

Returns a simpler status-focused view:

```json
{
  "amount": "200",
  "currency": "ZAR",
  "timestamp": "2022-04-29T09:42:25.922673Z",
  "transactionId": "969534114340323328",
  "status": "COMPLETE",
  "direction": "RECEIVE"
}
```

**Key differences from the identifier endpoint:**

| Field | By identifier | By transactionId |
|---|---|---|
| `amount` | Number | String |
| `type` / `direction` | `type`: `CREDIT` / `DEBIT` | `direction`: `RECEIVE` / `SEND` |
| `status` | May be absent | Always present |

**Prefer `GET /v1/pay/transactionid/{id}` for polling after a send** — it
always includes `status` and is the most reliable way to confirm completion.

**Both endpoints return error `-15407`** (`"Cannot find payment"`) if the
identifier or transactionId does not match any payment on the account.
