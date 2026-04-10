# VALR Exchange Agent Skill

An [Agent Skill](https://agentskills.io) that lets AI agents interact with the [VALR](https://valr.com) cryptocurrency exchange — querying market data, managing orders, reviewing account activity, and more — without needing prior knowledge of VALR's API or authentication scheme.

## Requirements

- Python 3.8+ (standard library only, no packages to install)
- A VALR account for authenticated operations — [sign up at valr.com](https://valr.com)

## API keys

Market data endpoints (prices, pairs, order book) work without credentials. For account operations, generate an API key under **Settings → API Keys** in the VALR app, then set:

```bash
export VALR_API_KEY=your_api_key
export VALR_API_SECRET=your_api_secret
```

> **⚠️ Keep your credentials safe.** API keys can authorise trades and withdrawals on your behalf. Never commit them to version control. When creating keys, grant only the permissions your workflow requires.

### OpenClaw

OpenClaw's skill configuration provides a single [`apiKey` SecretRef](https://docs.openclaw.ai/gateway/secrets) per skill for credential injection. Since VALR requires both an API key and an API secret, this skill supports combining them into one colon-separated value:

```bash
export VALR_API_KEY_SECRET_COMBINED=your_api_key:your_api_secret
```

When set, this takes precedence over `VALR_API_KEY` / `VALR_API_SECRET`. See [`references/openclaw.md`](references/openclaw.md) for the full setup guide including secure credential storage with 1Password.

## Installation

This skill follows the [Agent Skills](https://agentskills.io) standard and works with any compatible coding agent. Place this repository in your agent's skills directory — the agent discovers and loads `SKILL.md` automatically.

**Global install** (available in every project):

```bash
# Claude Code
git clone https://github.com/valrdotcom/valr-agent-skills.git ~/.claude/skills/valr-exchange

# OpenCode (also scans ~/.claude/skills/)
git clone https://github.com/valrdotcom/valr-agent-skills.git ~/.config/opencode/skills/valr-exchange

# OpenClaw
git clone https://github.com/valrdotcom/valr-agent-skills.git ~/.openclaw/workspace/skills/valr-exchange
```

**Project-level install** (scoped to a single repo):

```bash
git clone https://github.com/valrdotcom/valr-agent-skills.git .claude/skills/valr-exchange
```

This path is recognised by both Claude Code and OpenCode.

**Other agents:** Any agent that supports the Agent Skills standard can use this skill. Check your agent's documentation for its skills directory path. See [agentskills.io](https://agentskills.io) for a list of compatible agents.

## Capabilities

The skill covers the following areas of the VALR API:

#### Market Data
- View supported currencies, trading pairs, and pair constraints (tick size, min/max order sizes)
- Get current market summaries, order book depth, and bid/ask spreads
- Retrieve historical OHLCV candle data and mark price data for futures
- Look up supported order types per pair

#### Trading
- Place limit, market, stop-limit, and simple buy/sell orders
- Modify open orders (price, quantity)
- Cancel orders (single, per-pair, or all)
- Submit batch operations — up to 20 order placements, cancellations, and modifications in a single request
- Check order status and list open orders

#### Perpetual Futures
- View available futures pairs, funding rates, and open interest
- Get and set leverage per pair
- View open and closed positions with unrealised PnL
- Inspect position lifecycle history
- View funding payment history (paid/received)

#### Margin
- Check margin and futures account status
- View live margin metrics (collateral, available margin, PnL)
- Enable margin or futures trading on subaccounts

#### Trade & Order History
- View executed trade fills (all pairs or per-pair)
- Browse order history with status, pair, and date range filters
- Inspect full order lifecycle (all state transitions for a specific order)

#### Fees
- View maker, taker, and simple fee rates for all pairs
- Get pre-trade fee estimates via simple order quotes

#### Account & Balances
- Check balances across all currencies
- View API key permissions and scope
- Full account transaction ledger with filtering by currency and transaction type

#### Subaccounts
- Create, rename, list, and delete subaccounts
- Transfer funds between accounts
- View balances across all accounts in one call
- Cross-subaccount transaction history

#### Crypto Wallet
- Get deposit addresses (with network selection)
- View deposit and withdrawal history
- Check withdrawal fees, minimums, and availability
- Create withdrawals using whitelisted address book entries or raw addresses
- View and look up whitelisted withdrawal addresses
- Check withdrawal status

#### VALR Pay
- Look up your PayID
- Send instant payments to other VALR users
- Check payment limits, history, and status

#### Authentication
- Automatic HMAC-SHA512 request signing — agents don't need to understand the signing scheme
- Subaccount scoping via a simple `--subaccount-id` flag
- Graceful fallback for public endpoints when no credentials are set

## API reference

Full VALR API documentation is available at [docs.valr.com](https://docs.valr.com).

## Feedback

Feedback on this project can be submitted to the VALR engineering team via the [support site](https://support.valr.com/hc/en-us/requests/new?ticket_form_id=26250112047900)

## Legal Notice
This repository contains example code and developer tooling provided by VALR.

Use of this repository and any associated code, packages, skills, scripts or integrations is subject to VALR’s Public Code Terms of Service. The contents of this repository are provided for development and integration purposes only and are made available “as is” without warranty of any kind. VALR shall not be liable for any loss arising in connection with the use of this repository. You are solely responsible for reviewing, testing and securing any implementation before using it in production.

VALR Public Code Terms of Service: https://support.valr.com/hc/en-us/articles/26187053439772-Public-Code-Terms-of-Service
