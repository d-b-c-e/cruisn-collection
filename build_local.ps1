# Native compilation is shared; user preferences are runtime data, never build
# inputs. Release stages a fresh package. Personal explicitly deploys to the rig.
param(
    [ValidateSet('Release', 'Personal')][string]$Target = 'Release',
    [string]$MameRoot = 'E:\Source\mame-src',
    [string]$MsysRoot = 'E:\msys64',
    [ValidateRange(1, 64)][int]$Jobs = 18,
    [switch]$SkipNativeBuild,
    [switch]$NoMedia,
    [string]$Version = 'dev'
)
$ErrorActionPreference = 'Stop'
$nativeRoot = (Resolve-Path -LiteralPath $MameRoot).Path
$candidate = Join-Path $nativeRoot 'build\mingw-gcc\bin\x64\Release\vunit.exe'
$personal = Join-Path $nativeRoot 'vunit.exe'
& python (Join-Path $PSScriptRoot 'harness\sync_native.py') --mame $nativeRoot
if ($LASTEXITCODE -ne 0) { throw 'Native helpers are out of sync; synchronize and review them first' }

if (-not $SkipNativeBuild) {
    $oldMsystem = $env:MSYSTEM
    try {
        $env:MSYSTEM = 'MINGW64'
        & (Join-Path $MsysRoot 'usr\bin\bash.exe') -lc 'export OS=Windows_NT; cd "$(cygpath -u "$1")" && make SUBTARGET=vunit SOURCES=src/mame/midway/midvunit.cpp,src/mame/midway/midzeus.cpp NOWERROR=1 TOOLS=0 SEPARATE_BIN=1 REGENIE=1 -j"$2"' -- $nativeRoot $Jobs
        if ($LASTEXITCODE -ne 0) { throw 'Native build failed' }
    } finally { $env:MSYSTEM = $oldMsystem }
}
if (-not (Test-Path -LiteralPath $candidate)) { throw "Separate native candidate is missing: $candidate" }
$digest = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant()

if ($Target -eq 'Release') {
    # Does not deploy the candidate, read rig/, or upload anything to GitHub.
    & (Join-Path $PSScriptRoot 'make_release.ps1') -Version $Version -NoMedia:$NoMedia `
        -Emulator $candidate -RuntimeRoot $nativeRoot
    if (-not $?) { throw 'Release staging failed' }
} else {
    $running = Get-CimInstance Win32_Process | Where-Object {
        $_.Name -eq 'vunit.exe' -and $_.ExecutablePath -eq $personal
    }
    if ($running) { throw 'Close the personal game before deploying; its executable and settings were not changed' }
    if (Test-Path -LiteralPath $personal) {
        $oldDigest = (Get-FileHash -LiteralPath $personal -Algorithm SHA256).Hash.ToLowerInvariant()
        $backup = Join-Path $PSScriptRoot "build\personal\previous\$oldDigest"
        New-Item -ItemType Directory -Force $backup | Out-Null
        if (-not (Test-Path -LiteralPath (Join-Path $backup 'vunit.exe'))) {
            Copy-Item -LiteralPath $personal -Destination (Join-Path $backup 'vunit.exe')
        }
    }
    Copy-Item -LiteralPath $candidate -Destination $personal
    if ((Get-FileHash -LiteralPath $personal -Algorithm SHA256).Hash.ToLowerInvariant() -ne $digest) {
        throw 'Personal deployment hash mismatch'
    }
    Write-Host "Personal native build deployed: $digest. Stream Deck uses the source launcher; rig preferences are preserved."
}
