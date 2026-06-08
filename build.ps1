# build.ps1 - One-shot build for the x64dbg MCP plugin (+ optional server).
#
# Ensures the plugin SDK is present (fetch-sdk.ps1), then configures and builds the
# plugin with CMake/Ninja/clang-cl. Pass -Server to also build the TypeScript server,
# -Install to copy the built plugins into your x64dbg via install.ps1.
#
# Usage:
#   .\build.ps1                       # build both x64 + x32 plugins
#   .\build.ps1 -Arch x64            # x64 only
#   .\build.ps1 -Server              # also build the TS server
#   .\build.ps1 -Install             # build, then install into x64dbg
#   .\build.ps1 -ForceSdk            # re-download the SDK even if up to date

[CmdletBinding()]
param(
    [ValidateSet('x64', 'x32', 'both')] [string]$Arch = 'both',
    [switch]$Server,
    [switch]$Install,
    [switch]$ForceSdk
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot

# 1. SDK (headers + import libs) - offline-tolerant once cached.
& "$Root\plugin\fetch-sdk.ps1" -Force:$ForceSdk

# 2. Plugin(s).
Push-Location "$Root\plugin"
try {
    if ($Arch -in 'x64', 'both') {
        cmake --preset x64-release
        cmake --build --preset x64-release
        if ($LASTEXITCODE) { throw "x64 plugin build failed ($LASTEXITCODE)" }
    }
    if ($Arch -in 'x32', 'both') {
        cmake --preset x32-release
        cmake --build --preset x32-release
        if ($LASTEXITCODE) { throw "x32 plugin build failed ($LASTEXITCODE)" }
    }
} finally { Pop-Location }

# 3. Server (optional).
if ($Server) {
    Push-Location "$Root\server"
    try {
        if (-not (Test-Path node_modules)) { npm install }
        npm run build
        if ($LASTEXITCODE) { throw "server build failed ($LASTEXITCODE)" }
    } finally { Pop-Location }
}

# 4. Install (optional).
if ($Install) { & "$Root\install.ps1" -Arch $Arch }

Write-Host "`nBuild complete." -ForegroundColor Cyan
