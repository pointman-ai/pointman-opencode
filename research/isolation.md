# OpenCode 2.2.1 isolation research — 2026-10-29

No machine config/auth/data contents were read, copied or modified. Sources:

- Installed Homebrew formula: `/opt/homebrew/Cellar/opencode-v2/2.2.1/.brew/opencode-v2.rb`, official binary URL `https://opencode.ai/files/bin/2.2.1/opencode-darwin-arm64.zip` (archive SHA256 `9df6ca3d031565c61080c717374ba846d238ec5b1c411eebe6b1b85835998ffe`).
- [Global paths](https://github.com/anomalyco/opencode/blob/dev/packages/util/src/global.ts): config and data resolve separately; private config does not move credentials.
- [Config discovery](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/config/discovery.ts): project discovery can be disabled; system/MDM remains eligible.
- [Config loading](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/config.ts): explicit/inline config merges with other eligible sources; wellknown config loads independently.
- [Credential storage](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/credential.ts): credentials live in the shared data DB.
- [Instruction discovery plugin](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/config/plugin/instruction.ts): project instruction discovery is distinct from configured instruction entries.
- [MCP schema](https://github.com/anomalyco/opencode/blob/dev/packages/schema/src/mcp.ts): native remote/local configuration.
- [Official brand](https://opencode.ai/brand): mark source; approval still required for live use.

These URLs use mutable `dev`, retrieved through browser tooling. Fetching tag
v2.2.1 failed, and shell DNS blocks a source checkout. To avoid treating current
dev as the installed release, `installed-evidence.json` records small matching
JavaScript fragments, byte offsets and SHA256 from the installed binary itself.
This contains code only, not runtime data. Relevant findings are documented in
the README; the evidence file is intentionally not a full source extraction.

The installed CLI help was checked under entirely synthetic HOME/XDG roots:
version v2.2.1, `run --session` creates/resumes, `--format json`, `--auto`,
`--model`, and global `--standalone` all exist. `debug config --standalone`
failed before private-server readiness, so this work does not prove effective
configuration or instruction isolation in a running server.

A safe runtime needs machine-data resolution before private HOME, OpenCode MCP
conversion, sanitized ambient variables, and fail-closed treatment of remaining
system/MDM/wellknown sources. There is no verified CLI switch disabling all of
those sources. Data access and permission scope remain the parent/runtime owner's
responsibility; never read credential values to diagnose this.
