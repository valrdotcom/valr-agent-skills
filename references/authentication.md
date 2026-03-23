# Authentication

## Contents

- **API Key Permissions** — permission scopes and what they allow
- **Request Signing** — HMAC-SHA512 signing mechanics and required headers
- **Verification Test Vectors** — known-good inputs to validate a signing implementation
- **API Key Scope** — main account keys vs subaccount keys
- **Security Practices** — key management guidelines

## Overview

Public endpoints (under `/v1/public/*`) require no authentication. All other
endpoints require HMAC-SHA512 signed requests using an API key and secret.

Use `scripts/valr_request.py` — it handles signing automatically when
`VALR_API_KEY` and `VALR_API_SECRET` are set.

## API Key Permissions

API keys are scoped to specific permissions. Request only the permissions needed:

| Permission | What it allows |
|---|---|
| View | Read balances, orders, history, and market data |
| Trade | Place and cancel orders |
| Transfer | Transfer funds between subaccounts |
| Withdraw | Withdraw crypto and fiat |
| Link Bank Account | Link bank accounts for fiat deposits/withdrawals |

Generate API keys in your VALR account settings. 2FA must be enabled first.

## Request Signing

Every authenticated request requires three additional HTTP headers:

| Header | Value |
|---|---|
| `X-VALR-API-KEY` | Your API key |
| `X-VALR-SIGNATURE` | HMAC-SHA512 signature (see below) |
| `X-VALR-TIMESTAMP` | Current Unix timestamp in milliseconds |

The signature is computed over this concatenated string:

```
timestamp + VERB + path + body + subaccountId
```

Where:
- `timestamp` — milliseconds since Unix epoch (same value as the header)
- `VERB` — uppercase HTTP method: `GET`, `POST`, `PUT`, `DELETE`
- `path` — full path including query string, e.g. `/v1/account/balances`
- `body` — JSON request body as a string; empty string if no body
- `subaccountId` — subaccount ID string; empty string if not impersonating

Python implementation (matches what `scripts/valr_request.py` uses):

```python
import hashlib
import hmac

def sign_request(api_secret, timestamp, verb, path, body="", subaccount_id=""):
    payload = str(timestamp) + verb.upper() + path + body + subaccount_id
    return hmac.new(
        api_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()
```

## Verification Test Vectors

Use these known-good inputs to verify a signing implementation:

**GET request:**

| Parameter | Value |
|---|---|
| API Secret | `4961b74efac86b25cce8fbe4c9811c4c7a787b7a5996660afcc2e287ad864363` |
| Timestamp | `1558014486185` |
| Verb | `GET` |
| Path | `/v1/account/balances` |
| Body | *(empty string)* |

Expected signature:
```
9d52c181ed69460b49307b7891f04658e938b21181173844b5018b2fe783a6d4c62b8e67a03de4d099e7437ebfabe12c56233b73c6a0cc0f7ae87e05f6289928
```

**POST request:**

| Parameter | Value |
|---|---|
| API Secret | `4961b74efac86b25cce8fbe4c9811c4c7a787b7a5996660afcc2e287ad864363` |
| Timestamp | `1558017528946` |
| Verb | `POST` |
| Path | `/v1/orders/market` |
| Body | `{"customerOrderId":"ORDER-000001","pair":"BTCUSDC","side":"BUY","quoteAmount":"80000"}` |

Expected signature:
```
09f536e3dfdad58443f16010a97a0a21ad27486b7b8d6d4103170d885410ed77f037f1fa628474190d4f5c08ca12c1acc850901f1c2e75c6d906ec3b32b008d0
```

## API Key Scope

API keys on VALR are issued either on the **main account** or on a specific
**subaccount**. The key type determines how requests are scoped:

**Main account key** (`isSubAccount: false`)
- Operates on the main account by default.
- Can act on behalf of any subaccount by passing the subaccount ID:

  | Header | Value |
  |---|---|
  | `X-VALR-SUB-ACCOUNT-ID` | The target subaccount's ID |

  The subaccount ID must also be appended to the signing string (after the
  body). `scripts/valr_request.py` handles both via the `--subaccount-id` flag.

**Subaccount key** (`isSubAccount: true`)
- Automatically scoped to the subaccount it was issued on.
- No `X-VALR-SUB-ACCOUNT-ID` header is needed or expected.
- Cannot access other subaccounts or the main account.

To check which type of key you are using:

```bash
python3 scripts/valr_request.py GET /v1/account/api-keys/current
```

The `isSubAccount` field in the response indicates whether the key is scoped to
a subaccount. If `true`, the key already operates on that subaccount directly.

When using `valr_request.py`, pass `--subaccount-id ID` to scope any request
to a subaccount. The script sets the `X-VALR-SUB-ACCOUNT-ID` header and
includes the ID in the signing string automatically (see the signing formula
in the Request Signing section above). No manual header or signature changes
are needed.

Some endpoints only operate on the primary account and will return 401 if a
subaccount ID is included.

## Security Practices

- Never send your API secret in a request — it is only used locally to generate signatures.
- Store keys in environment variables, not in code or config files.
- Use the minimum permission scope needed for the task.
- Delete and regenerate keys immediately if they may be compromised.
- Each request must use a fresh timestamp and a freshly computed signature.
