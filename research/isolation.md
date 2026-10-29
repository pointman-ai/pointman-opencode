# OpenCode 2.2.1 isolation research — 2026-10-29

No machine config/auth/data contents were read, copied or modified. Sources:

- Installed Homebrew formula: `/opt/homebrew/Cellar/opencode-v2/2.2.1/.brew/opencode-v2.rb`, official binary URL `https://opencode.ai/files/bin/2.2.1/opencode-darwin-arm64.zip` (archive SHA256 `9df6ca3d031565c61080c717374ba846d238ec5b1c411eebe6b1b85835998ffe`).
- [Global paths](https://github.com/anomalyco/opencode/blob/dev/packages/util/src/global.ts): config and data resolve separately; private config does not move credentials.
- [Config discovery](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/config/discovery.ts): project discovery can be disabled; system/MDM remains eligible.
- [Config loading](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/config.ts): explicit/inline config merges with other eligible sources; wellknown config loads independently.
- [Credential storage](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/credential.ts): credentials live in the shared data DB.
- [Instruction discovery plugin](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/config/plugin/instruction.ts): project instruction discovery is distinct from configured instruction entries.
- [MCP schema](https://github.com/anomalyco/opencode/blob/dev/packages/schema/src/mcp.ts): native remote/local configuration.
- [Official brand](https://opencode.ai/brand): mark source; see ICON-SOURCE.md for the shipped official asset.

These URLs use mutable `dev`, retrieved through browser tooling. Fetching tag
v2.2.1 failed, and shell DNS blocks a source checkout. To avoid treating current
dev as the installed release, `installed-evidence.json` records small matching
JavaScript fragments, byte offsets and SHA256 from the installed binary itself.
This contains code only, not runtime data. Relevant findings are documented in
the README; the evidence file is intentionally not a full source extraction.

The installed CLI help was checked under entirely synthetic HOME/XDG roots:
version v2.2.1, `run --session` creates/resumes, `--format json`, `--auto`,
`--model`, and global `--standalone` all exist.

Runtime review on mac-m4 then verified effective config under the private
XDG_CONFIG_HOME: only the agent's config was loaded, excluding the machine's MCP.
A signed-in remember/recall pair confirmed explicit session reuse. Real run and
error captures are retained in the Pointman node's stream goldens.

The implementation resolves machine data before private HOME, converts MCP to
OpenCode's native format, and removes conflicting ambient variables. It does not
inspect the credentials database or launch a Python preflight. System/remote
managed configuration is outside this integration's configuration-isolation scope.

The installed-code evidence file also records config-discovery paths that were
investigated during development. Those excerpts describe upstream capabilities;
they do not imply runtime metadata checks in this extension or the node.
