# Official binary provenance

OpenCode 2.2.1 is MIT licensed. [Source](https://github.com/anomalyco/opencode),
[license](https://github.com/anomalyco/opencode/blob/dev/LICENSE),
[official site](https://opencode.ai). `LICENSE.opencode` retains the upstream
copyright and MIT terms. Our extension's own code is covered by `LICENSE`.

`upstream.json` pins the four official archive URLs and SHA256 values from the
installed official Homebrew `opencode-v2` 2.2.1 formula. The pin includes x64
baseline binaries. Do not replace version or checksums without reviewing upstream.
These archives have not been downloaded or repacked in this restricted session.

The manual, artifact-only GitHub workflow calls `scripts/repack.py`. It verifies
the downloaded archive before parsing, selects exactly one regular `opencode`
executable without extracting paths, and makes a deterministic gzip/tar containing
`opencode-<platform>` at its root. That name matches Pointman's existing release
installer. Each archive includes the upstream license and source manifest, and
has a SHA256 sidecar. It never executes the downloaded binary.

There is no automatic publishing job. After review, release-extension must attach
these assets to the extension release and verify GitHub exposes each asset's
SHA256 digest; the node refuses a release asset without that digest. A repository
and release do not exist yet. Runtime sign-in, macOS code signing/quarantine,
Linux/NixOS compatibility and real archive contents remain unverified. Linux musl
has no pin here and must not silently use the glibc builds as verified support.

The OpenCode trademark is separate: see ICON-SOURCE.md. A license for source code
does not constitute approval to use the mark in the apps.
