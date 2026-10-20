# Recover / Install from neohiro/opencode (main / PR #2)

Bundle merged to `main`: `0a63792d586e7d8649432731c986903fef319163`
Repo: `neohiro/opencode`
Branch: `main` (default; `dev` deleted after merge)

## What's included (reproducible setup for another device)
- `.opencode/bin/edit` — exact / CRLF-normalized / whitespace-tolerant file edits; schema aliases (`path`/`filePath`, `oldString`/`old_string`); closest-line diagnostics; BOM-preserving; offset-safe (fixes previous CRLF+fuzzy corruption bug).
- `.opencode/bin/bash` — true bash (Git Bash preferred) with broken-fork (`0xC0000142`) fallback; supports `workdir`, `timeout`, `&&`, `||`, pipes; JSON output.
- `.opencode/bin/grep` — pure-Python fallback + ripgrep; avoids 65536-byte JSON overflow; handles Windows absolute paths; structured JSON.
- `.opencode/bin/shell` — delegates to bash; absolute-path safe; supports `workdir`.
- `.opencode/plugins/github-context-augment.ts` — session-start plugin.
- `opencode.jsonc` — workspace MCP + plugin config (context7, filesystem, sequential-thinking, git, memory, github, time, playwright + plugin).
- `tests/test_opencode_bin.py` — regression tests.
- `docs/session_errors_2026-10-20.txt` — 173 recent error signatures.

## Note: `AGENTS.md`
Upstream root `AGENTS.md` preserved; workspace agent identity placed at `.opencode/AGENTS.md`.

## Quick install (new device / fresh opencode)
```
# Clone / checkout this repo (main branch)
git clone https://github.com/neohiro/opencode.git ~/opencode-setup
# OR download bundle zip / unpack

# Linux / macOS
bash <(curl -sL https://raw.githubusercontent.com/neohiro/opencode/main/deploy_target/install.sh) 2>/dev/null || \
  cp -r ~/opencode-setup/.opencode ~/.config/opencode/
  cp ~/opencode-setup/opencode.jsonc ~/.config/opencode/
  echo 'export PATH="$HOME/.config/opencode/bin:$PATH"' >> ~/.bashrc

# Windows PowerShell
# (use install.ps1; it copies .opencode/ to %USERPROFILE%\.config\opencode\ and updates $env:PATH for bin/)
```

## What's NOT covered by this bundle (but exists globally on the owner device)
- Global provider keys / endpoints (`~/.config/opencode/opencode.jsonc` has Ox Alpha / Tokenra settings — use those separately).
- Auto-resume plugin files (live at `repos/auto-resume/` / `~/.config/opencode/plugins/auto-resume.js` on owner's device).
- MCS (context7, sequential-thinking) auth keys — set `CONTEXT7_API_KEY` globally.
- Skill definitions (`skills` folder under `~/.config/opencode/skills`) — bring over separately if needed.

## Branch / protection status
- `main` default branch (set via API).
- `dev` deleted.
- Protection restored: 1 required review, enforce admins enabled, no force pushes/deletions.
- PR #2 merged (`0a63792d`) — settings deployed.
