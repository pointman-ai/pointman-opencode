# Pointman OpenCode client

A standalone client extension for OpenCode **2.2.1**, using the machine's existing
OpenCode sign-in. Local review only: no remote repository, release or installation
has been created. The icon is a review candidate until approved.

Requires Pointman node **0.4.3 or newer with AGC-75 support**: `opencode-stream`,
machine-data path preservation, native MCP conversion and isolation guards.
The manifest alone does not provide these features; older nodes must reject it.
The runtime owner confirmed the 0.4.3 release floor.

## Install and sign in

Install the official OpenCode v2 CLI for the machine, then run `opencode auth login`
in the ordinary machine environment. The release installer uses this repository’s checksum-verified repacks of official
2.2.1 binaries; it does not install npm’s potentially different CLI generation. mac-m4 currently
has `/opt/homebrew/bin/opencode`, version 2.2.1. Other platforms are unverified.
No key form or vault secret is defined by this extension.

The repository has no published release yet. The artifact-only `repack.yml`
workflow downloads pinned official archives and produces node-compatible archives
plus checksums. It does not publish a release. The existing release-extension
workflow remains the publication path after review. See [UPSTREAM.md](UPSTREAM.md).

## A wake

The runtime starts a private server for one wake, with closed stdin:

```text
opencode run --standalone --format json --session <node-chosen-id> --auto -m <provider/model> -- <prompt>
```

Both first and later wakes use the same explicit `--session` argument. The CLI
creates the ID if missing and resumes it otherwise. Never use `--continue` or
attach to the person's background service. The node must generate an ID accepted
by OpenCode's native session schema (the runtime owns that validation).
The prompt is one argv item after `--`, including when it starts with a dash.
The supplied model wins; otherwise private config selects
`zai-coding-plan/glm-5.3`. Plan mode uses `--agent plan` without `--auto`;
acceptEdits currently maps to OpenCode's `--auto`, which is broader than edit-only.
Instructions are appended to the prompt by the node, avoiding file discovery.

## Isolation contract

Before replacing HOME, the node resolves the machine data root from the original
absolute `XDG_DATA_HOME`, falling back to original HOME plus `.local/share`.
It passes that exact root as `XDG_DATA_HOME`. OpenCode v2 stores credentials in its
data database; `auth.json` is a legacy import. Do not copy credentials or databases,
symlink sign-in files, edit the user's config, or print resolved config/auth.

Each agent has private `<node-state>/homes/opencode/<handle>` as HOME, config,
cache and state paths set by the manifest. The runtime must remove ambient
`OPENCODE_DB` (otherwise it overrides the preserved machine DB), service connection,
model/source overrides and other conflicting OpenCode environment values before
applying the manifest. Both project-disable variable names are set because the
new name takes precedence over the legacy name. Claude compatibility is disabled;
private HOME also excludes machine `.agents` and `.claude` discovery.

The node writes only the private `.config/opencode/opencode.json`, replacing its
entire MCP table on every launch so revoked grants disappear. OpenCode needs
`type: remote`, `url`, `headers`, `oauth: false` for Pointman's HTTP MCP entry.
Local entries use `type: local`, an argv-array `command`, and `environment`.
Generic key renaming cannot perform this conversion. See the synthetic fixture
in `tests/fixtures/mcp-contract.json`.

**Release blocker:** OpenCode also loads system/MDM configuration and
credential-linked wellknown remote configuration. Private config and project
flags do not suppress these sources. The runtime must fail closed when they
could supply foreign configuration; do not claim complete isolation from just
`OPENCODE_CONFIG_CONTENT`. System/MDM paths were absent on this machine when
checked. Shared-data/wellknown checks require authorized machine-data access and
were not performed here. The CLI has no verified environment flag to turn all
these sources off. A guard must also account for sources changing during a run.

Shared machine data includes sessions, logs and credentials, so this is config
isolation, not a security boundary between mutually untrusted agents. OpenCode
may migrate or refresh that database; permission to run it must include its normal
data and lock writes. Do not bypass a sandbox denial by copying machine data.

## Offline checks

```sh
python3 -m unittest discover -s tests -v
```

Checks parse the manifest, verify explicit resume and prompt boundaries, prevent
vault-key delivery and machine-data hardcoding, and check synthetic MCP data.
If `opencode` is installed, help/version probes run with entirely temporary HOME
and XDG roots and a minimal environment. They never run a prompt, sign in, connect
to MCP, or read machine data. Set `OPENCODE_CHECK_BINARY` to an absolute executable
to check a particular installation. Native stream decoding tests belong in the
Pointman node; this repo does not invent a captured native stream.

The installed binary reported v2.2.1 and confirmed all required run flags.
`debug config --standalone` could not start its private server in this sandbox;
resolved config, actual sign-in reuse, model calls, two-wake resume, OAuth refresh,
MCP tools, usage-limit events, hosted CI and Linux/NixOS were not verified here.

Sources and exact installed-code evidence are in [research/isolation.md](research/isolation.md).
