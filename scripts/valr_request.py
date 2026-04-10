#!/usr/bin/env python3
"""
valr_request.py — Make authenticated or public requests to the VALR API.

Signs requests automatically when VALR_API_KEY and VALR_API_SECRET are set.
Falls back to unsigned requests when credentials are absent (suitable for
public endpoints).

The actual HTTP call is made via curl. Curl's stdout and stderr are passed
through directly to the caller.

Usage:
  python3 scripts/valr_request.py METHOD PATH [--body JSON] [--subaccount-id ID]

Examples:
  python3 scripts/valr_request.py GET /v1/account/balances
  python3 scripts/valr_request.py GET /v1/public/pairs
  python3 scripts/valr_request.py POST /v1/orders/limit --body '{"side":"BUY","quantity":"0.0001","price":"500000","pair":"BTCUSDC","postOnly":false,"timeInForce":"GTC"}'
  python3 scripts/valr_request.py GET /v1/account/balances --subaccount-id 12345
  python3 scripts/valr_request.py GET /v1/public/pairs --verbose

Environment variables:
  VALR_API_KEY_SECRET_COMBINED — API key and secret joined by a colon
                                  (key:secret). When set and non-empty, takes
                                  precedence over VALR_API_KEY / VALR_API_SECRET.
  VALR_API_KEY    — API key (required for authenticated endpoints)
  VALR_API_SECRET — API secret (required for authenticated endpoints)
  VALR_BASE_URL   — Base URL (default: https://api.valr.com)

Exit codes:
  0 — Request completed (check the JSON body for API-level errors)
  1 — Invalid arguments or configuration error
  Non-zero — curl error (network failure, DNS resolution, etc.)
"""

import argparse
import hashlib
import hmac
import os
import subprocess
import sys
import time


DEFAULT_BASE_URL = "https://api.valr.com"


def sign_request(
    api_secret: str,
    timestamp: int,
    verb: str,
    path: str,
    body: str = "",
    subaccount_id: str = "",
) -> str:
    """Generate HMAC-SHA512 signature for a VALR API request.

    Signature input: timestamp + verb.upper() + path + body + subaccount_id
    All values concatenated as UTF-8 strings before hashing.
    """
    payload = str(timestamp) + verb.upper() + path + body + subaccount_id
    return hmac.new(
        api_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()


def make_request(
    method: str,
    path: str,
    body: str = "",
    subaccount_id: str = "",
    verbose: bool = False,
) -> int:
    """Make a VALR API request via curl, passing through stdout and stderr.

    Returns curl's exit code directly.
    """
    base_url = os.environ.get("VALR_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    url = base_url + path

    combined = os.environ.get("VALR_API_KEY_SECRET_COMBINED", "")
    if combined:
        api_key, _, api_secret = combined.partition(":")
    else:
        api_key = os.environ.get("VALR_API_KEY", "")
        api_secret = os.environ.get("VALR_API_SECRET", "")
    authenticated = bool(api_key and api_secret)

    cmd = ["curl", "-s", "-S"]
    if verbose:
        cmd.append("-v")
    cmd += ["-X", method.upper()]

    cmd += ["-H", "Content-Type: application/json"]
    cmd += ["-H", "User-Agent: valr-agent-skill/0.4"]

    if authenticated:
        timestamp = int(time.time() * 1000)
        signature = sign_request(
            api_secret, timestamp, method, path, body, subaccount_id
        )
        cmd += ["-H", f"X-VALR-API-KEY: {api_key}"]
        cmd += ["-H", f"X-VALR-SIGNATURE: {signature}"]
        cmd += ["-H", f"X-VALR-TIMESTAMP: {str(timestamp)}"]
        if subaccount_id:
            cmd += ["-H", f"X-VALR-SUB-ACCOUNT-ID: {subaccount_id}"]

    if body:
        cmd += ["-d", body]

    cmd.append(url)

    result = subprocess.run(cmd)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Make authenticated or public requests to the VALR API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "method",
        metavar="METHOD",
        help="HTTP method: GET, POST, PUT, DELETE, PATCH",
    )
    parser.add_argument(
        "path",
        metavar="PATH",
        help="API path including query string, e.g. /v1/account/balances",
    )
    parser.add_argument(
        "--body",
        default="",
        metavar="JSON",
        help="JSON request body (for POST/PUT/PATCH requests)",
    )
    parser.add_argument(
        "--subaccount-id",
        default="",
        metavar="ID",
        help="Subaccount ID to impersonate (primary account API key required)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Pass -v to curl for verbose output (headers, connection info)",
    )

    args = parser.parse_args()

    if args.body.startswith("@"):
        print(
            "Error: --body must be a JSON string. File references (@filepath) "
            "are not supported and will not be sent.",
            file=sys.stderr,
        )
        return 1

    method = args.method.upper()
    valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
    if method not in valid_methods:
        print(
            f"Error: METHOD must be one of {', '.join(sorted(valid_methods))}.",
            file=sys.stderr,
        )
        return 1

    if not args.path.startswith("/"):
        print(
            "Error: PATH must start with '/', e.g. /v1/account/balances",
            file=sys.stderr,
        )
        return 1

    return make_request(
        args.method, args.path, args.body, args.subaccount_id, args.verbose
    )


if __name__ == "__main__":
    sys.exit(main())
