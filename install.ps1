#!/usr/bin/env pwsh
# Recover opencode settings / mods from this bundle to global config (Windows).
$target = if ($args[0]) { $args[0] } else { "$env:USERPROFILE\.config\opencode" }
New-Item -ItemType Directory -Force -Path "$target\bin" | Out-Null
New-Item -ItemType Directory -Force -Path "$target\plugins" | Out-Null
Copy-Item ".opencode\bin\*" -Destination "$target\bin\" -Force
Copy-Item ".opencode\plugins\*" -Destination "$target\plugins\" -Force
Copy-Item "opencode.jsonc" -Destination "$target\" -Force
if (Test-Path ".opencode\AGENTS.md") { Copy-Item ".opencode\AGENTS.md" -Destination "$target\" -Force }

$env:PATH = "$target\bin;$env:PATH"
Write-Host "Installed to $target (edit / bash / grep / shell)"
Get-ChildItem "$target\bin"
