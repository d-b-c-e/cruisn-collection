# Assemble a self-contained, shareable release folder + zip.
#   .\make_release.ps1            (uses dev-machine defaults)
# Produces build\release\CruisnCollection\ and build\CruisnCollection-<date>.zip
#
# The release contains NO ROMs and NO game art/music - the player supplies
# ROMs; art/music degrade to generated fallbacks. It DOES contain:
#   - CruisnCollection.exe (PyInstaller-frozen shell - no Python needed)
#   - vunit.exe (statically-linked; GPL source = patch\ + source\ + MAME)
#   - FFB Arcade Plugin files (GPL-3.0, license included, GUID blanked)
#   - NVRAM fixtures, setup.ps1, docs
$ErrorActionPreference = "Stop"
$root   = $PSScriptRoot
$vunit  = if ($env:CRUISN_VUNIT) { $env:CRUISN_VUNIT } else { "E:\Source\mame-src\vunit.exe" }
$vdir   = Split-Path $vunit
$dist   = Join-Path $root "build\dist\CruisnCollection"
$rel    = Join-Path $root "build\release\CruisnCollection"

Write-Host "== building release ==" -ForegroundColor Cyan

# 1. frozen shell (rebuild if missing)
if (-not (Test-Path (Join-Path $dist "CruisnCollection.exe"))) {
    Write-Host "  freezing shell (PyInstaller)..."
    & python -m PyInstaller --noconfirm --onedir --noconsole --name CruisnCollection `
        --distpath (Join-Path $root "build\dist") --workpath (Join-Path $root "build\work") `
        --specpath (Join-Path $root "build") (Join-Path $root "harness\collection.py") | Out-Null
}

# 2. layout
if (Test-Path $rel) {
    try { Remove-Item -Recurse -Force $rel -ErrorAction Stop }
    catch {
        # something (Explorer?) holds the old folder - build beside it
        $rel = "$rel-" + (Get-Date -Format "HHmmss")
        Write-Host "  old release folder locked; building $rel" -ForegroundColor Yellow
    }
}
New-Item -ItemType Directory -Force $rel | Out-Null
Copy-Item -Recurse (Join-Path $dist "*") $rel
foreach ($d in "fixtures", "patch", "docs") { Copy-Item -Recurse (Join-Path $root $d) (Join-Path $rel $d) }
New-Item -ItemType Directory -Force (Join-Path $rel "roms") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $rel "source") | Out-Null
foreach ($d in "harness", "gpu", "lua") { Copy-Item -Recurse (Join-Path $root $d) (Join-Path $rel "source\$d") }
Copy-Item (Join-Path $root "setup.ps1") $rel

# 3. emulator + FFB plugin
Copy-Item $vunit (Join-Path $rel "vunit.exe")
foreach ($f in "dinput8.dll", "SDL2.dll", "MAME64.dll") {
    if (Test-Path (Join-Path $vdir $f)) { Copy-Item (Join-Path $vdir $f) $rel }
    else { Write-Host "  [!] $f not found beside vunit.exe - player must run setup's FFB download" -ForegroundColor Yellow }
}
if (Test-Path (Join-Path $vdir "FFBPlugin.ini")) {
    # ship the tuned ini but blank the machine-specific wheel GUID + logging
    (Get-Content (Join-Path $vdir "FFBPlugin.ini")) `
        -replace '^DeviceGUID=.*', 'DeviceGUID=' `
        -replace '^Logging=.*', 'Logging=0' |
        Set-Content (Join-Path $rel "FFBPlugin.ini")
}
try {
    Invoke-WebRequest -UseBasicParsing -OutFile (Join-Path $rel "FFBPLUGIN-LICENSE.txt") `
        "https://raw.githubusercontent.com/Boomslangnz/FFBArcadePlugin/master/LICENSE"
} catch {
    "FFB Arcade Plugin by Boomslangnz - GPL-3.0 - https://github.com/Boomslangnz/FFBArcadePlugin" |
        Set-Content (Join-Path $rel "FFBPLUGIN-LICENSE.txt")
}

# 4. README
@"
CRUIS'N COLLECTION
==================
1. Put your own MAME 0.286 ROM sets in roms\
   (crusnusa.zip, crusnwld.zip, offroadc.zip, crusnexo.zip)
2. Run setup.ps1 once (right-click -> Run with PowerShell)
3. Double-click CruisnCollection.exe

Wheel setup, CRT effects: SETTINGS inside the launcher.
In-game: 5=coin, 1=start, F9=CRT toggle, Esc=back to launcher.
Full docs: docs\INSTALL.md.

This package contains no ROMs and no Midway assets. Emulator: MAME
(GPL-2.0+), patch series in patch\, launcher source in source\.
FFB Arcade Plugin (c) Boomslangnz, GPL-3.0 (FFBPLUGIN-LICENSE.txt).
"@ | Set-Content (Join-Path $rel "README.txt")

# 5. zip
$stamp = Get-Date -Format "yyyy-MM-dd"
$zip = Join-Path $root "build\CruisnCollection-$stamp.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path $rel -DestinationPath $zip
$mb = [math]::Round((Get-Item $zip).Length / 1MB, 0)
Write-Host "release: $rel" -ForegroundColor Green
Write-Host "zip:     $zip ($mb MB)" -ForegroundColor Green
