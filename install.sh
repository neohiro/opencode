#!/bin/bash
set -euo pipefail
# Recover opencode settings / mods from this bundle to global config.
# Usage: bash install.sh [TARGET_DIR]  # default: ~/.config/opencode

TARGET="${1:-$HOME/.config/opencode}"
mkdir -p "$TARGET/bin"

cp -r ./.opencode/bin/* "$TARGET/bin/" 2>/dev/null || cp -r .opencode/bin/* "$TARGET/bin/"
cp -r ./.opencode/plugins/* "$TARGET/plugins/" 2>/dev/null || cp -r .opencode/plugins/* "$TARGET/plugins/" 2>/dev/null || true
cp opencode.jsonc "$TARGET/"
cp .opencode/AGENTS.md "$TARGET/" 2>/dev/null || true

# Add bin/ to PATH (non-destructive for interactive shells)
if command -v bash >/dev/null 2>&1; then
    echo 'export PATH="$HOME/.config/opencode/bin:$PATH"' >> "$HOME/.profile"
fi

# Confirm
ls -la "$TARGET/bin/"
echo "Installed to $TARGET (edit / bash / grep / shell available)"
