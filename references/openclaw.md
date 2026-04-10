# OpenClaw Setup

This file covers:

- **Why a combined credential variable** — OpenClaw's single `apiKey` SecretRef per skill
- **Secure configuration** — storing credentials in 1Password or another secrets manager via SecretRef
- **Environment-only setup** — using an env var when a secrets manager is not available

## Combined Credentials

OpenClaw provides each skill with a single `apiKey` credential via the
`skills.entries.<name>.apiKey` config field. The skill's `primaryEnv` metadata
determines which environment variable receives this value at runtime.

This skill sets `primaryEnv` to `VALR_API_KEY_SECRET_COMBINED`. Since the VALR
API requires both an API key and an API secret for authentication, the two
values are combined into a single string separated by a colon:

```
key:secret
```

The script splits on the first colon, so if the secret itself contains a colon
it is handled correctly.

## Secure Setup with 1Password

Store the combined `key:secret` value as a single item in 1Password, then
reference it via an exec SecretRef in `~/.openclaw/openclaw.json`:

```json5
{
  secrets: {
    providers: {
      valr: {
        source: "exec",
        command: "/opt/homebrew/bin/op",
        allowSymlinkCommand: true,
        trustedDirs: ["/opt/homebrew"],
        args: ["read", "op://Vault/VALR API/combined"],
        passEnv: ["HOME"],
        jsonOnly: false,
      },
    },
  },
  skills: {
    entries: {
      "valr-exchange": {
        apiKey: { source: "exec", provider: "valr", id: "value" },
      },
    },
  },
}
```

Adjust `op://Vault/VALR API/combined` to match your 1Password vault, item name,
and field name.

Other SecretRef sources (`env`, `file`) also work. See the
[OpenClaw secrets documentation](https://docs.openclaw.ai/gateway/secrets) for
the full list of supported providers.

## Environment-Only Setup

If a secrets manager is not available, set the combined variable directly:

```bash
export VALR_API_KEY_SECRET_COMBINED=your_api_key:your_api_secret
```

This is less secure than a SecretRef — prefer a secrets manager when possible.
