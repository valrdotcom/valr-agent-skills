# Authentication

## Contents

- **API Key Permissions** — permission scopes and what they allow
- **Request Signing** — how authentication works (handled by the script)
- **API Key Scope** — main account keys vs subaccount keys
- **Security Practices** — key management guidelines

## Overview

Public endpoints (under `/v1/public/*`) require no authentication. All other
endpoints require HMAC-SHA512 signed requests using an API key and secret.

Use `{baseDir}/scripts/valr_request.py` — it handles signing automatically when
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

All non-public endpoints require HMAC-SHA512 signed requests. The signature
covers the timestamp, HTTP method, path, request body, and subaccount ID (if
any). **`{baseDir}/scripts/valr_request.py` handles all authentication automatically** —
do not construct signed requests manually. Never build your own curl commands,
HTTP requests, or code that references `VALR_API_KEY` or `VALR_API_SECRET`.
Always use the script.

If you encounter 401 or 403 errors on authenticated endpoints, verify that
`VALR_API_KEY` and `VALR_API_SECRET` are set correctly in the environment.

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
  body). `{baseDir}/scripts/valr_request.py` handles both via the `--subaccount-id` flag.

**Subaccount key** (`isSubAccount: true`)
- Automatically scoped to the subaccount it was issued on.
- No `X-VALR-SUB-ACCOUNT-ID` header is needed or expected.
- Cannot access other subaccounts or the main account.

To check which type of key you are using:

```bash
python3 {baseDir}/scripts/valr_request.py GET /v1/account/api-keys/current
```

The `isSubAccount` field in the response indicates whether the key is scoped to
a subaccount. If `true`, the key already operates on that subaccount directly.

**Important caveats:**

- Do not pass `--subaccount-id` when using a subaccount key. The key is already
  scoped — adding the flag will cause the request to fail.
- When using a subaccount key, refer to the account as "your account" or "your
  subaccount" — not "your main account" or "primary account". The primary
  account is a different account that this key cannot access.
- A subaccount key cannot call subaccount management endpoints (list, create,
  delete, transfer between accounts). These require a main account key.

**Using `--subaccount-id` (main account keys only):** When using a main account
key, pass `--subaccount-id ID` to scope any request to a subaccount. The script
sets the `X-VALR-SUB-ACCOUNT-ID` header and includes the ID in the request
signature automatically. No manual header or signature changes are needed.

Some endpoints only operate on the primary account and will return 401 if a
subaccount ID is included.

## Security Practices

- Never send your API secret in a request — it is only used locally to generate signatures.
- Store keys in environment variables, not in code or config files.
- Use the minimum permission scope needed for the task.
- Delete and regenerate keys immediately if they may be compromised.
- Each request must use a fresh timestamp and a freshly computed signature.
