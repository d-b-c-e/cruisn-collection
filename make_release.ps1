# Assemble a self-contained, shareable release folder + zip.
#   .\make_release.ps1            full release (menu art + music included -
#                                 LaunchBox/wanszai bundling precedent)
#   .\make_release.ps1 -NoMedia   clean variant: no art, no music (generated
#                                 fallback cards, silent menu)
# Produces build\release\CruisnCollection\ and build\CruisnCollection-<date>.zip
#
# Never contains ROMs. Always contains:
#   - CruisnCollection.exe (PyInstaller-frozen shell - no Python needed)
#   - vunit.exe (statically-linked; GPL source = patch\ + source\ + MAME)
#   - SDL2.dll (zlib license, included) - the emulator's own force feedback
#   - NVRAM fixtures, setup.ps1, docs
param([switch]$NoMedia, [string]$Version = "dev")
$ErrorActionPreference = "Stop"
$root   = $PSScriptRoot
$vunit  = if ($env:CRUISN_VUNIT) { $env:CRUISN_VUNIT } else { "E:\Source\mame-src\vunit.exe" }
$vdir   = Split-Path $vunit
$dist   = Join-Path $root "build\dist\CruisnCollection"
$rel    = Join-Path $root "build\release\CruisnCollection"

Write-Host "== building release ==" -ForegroundColor Cyan

# 1. frozen shell + setup GUI - ALWAYS re-frozen: a stale build\dist from
# an earlier session silently shipped a month-old launcher once
$glfwdll = & python -c "import glfw.library; print(glfw.library.glfw._name)"
foreach ($stale in (Join-Path $root "build\dist"), (Join-Path $root "build\work")) {
    if (Test-Path $stale) { Remove-Item -Recurse -Force $stale }
}
if (-not (Test-Path (Join-Path $dist "CruisnCollection.exe"))) {
    Write-Host "  freezing shell (PyInstaller)..."
    & python -m PyInstaller --noconfirm --onedir --noconsole --name CruisnCollection `
        --add-binary "$glfwdll;glfw" `
        --distpath (Join-Path $root "build\dist") --workpath (Join-Path $root "build\work") `
        --specpath (Join-Path $root "build") (Join-Path $root "harness\collection.py") | Out-Null
}
if (-not (Test-Path (Join-Path $root "build\dist\CruisnSetup.exe"))) {
    Write-Host "  freezing setup GUI (PyInstaller onefile)..."
    & python -m PyInstaller --noconfirm --onefile --noconsole --name CruisnSetup `
        --add-data "$(Join-Path $root 'harness\roms_manifest.json');." `
        --add-data "$(Join-Path $root 'lua\input_dump.lua');." `
        --hidden-import support_bundle --hidden-import dinput_axes `
        --distpath (Join-Path $root "build\dist") --workpath (Join-Path $root "build\work") `
        --specpath (Join-Path $root "build") (Join-Path $root "harness\cruisn_setup.py") | Out-Null
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
Copy-Item (Join-Path $root "build\dist\CruisnSetup.exe") $rel -ErrorAction SilentlyContinue
foreach ($d in "fixtures", "patch", "docs") { Copy-Item -Recurse (Join-Path $root $d) (Join-Path $rel $d) }
# The toolkit's force profiles. run_rig.deploy_force_profiles() copies this
# beside vunit.exe at every launch (backing up an edited one first), so the
# SETTINGS > FORCE FEEDBACK > FEEL row has real tunes to offer. Without it the
# emulator falls back to values equal to cruisn-vunit@1 and FEEL has one entry.
New-Item -ItemType Directory -Force (Join-Path $rel "lib	oolkit\profiles") | Out-Null
Copy-Item (Join-Path $root "lib	oolkit\profilesorce-profiles.ini") (Join-Path $rel "lib	oolkit\profiles")
Copy-Item (Join-Path $root "lib	oolkit\VERSION") (Join-Path $rel "lib	oolkit") -ErrorAction SilentlyContinue
# The starter file for a player's own tune. Shipped BESIDE vunit.exe so it is
# found without hunting, and in profiles\ so the launcher can put it back if
# it is deleted. Inert until renamed to force-profiles.user.ini.
New-Item -ItemType Directory -Force (Join-Path $rel "profiles") | Out-Null
Copy-Item (Join-Path $root "profilesorce-profiles.user.ini.example") (Join-Path $rel "profiles")
Copy-Item (Join-Path $root "profilesorce-profiles.user.ini.example") $rel
New-Item -ItemType Directory -Force (Join-Path $rel "roms") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $rel "source") | Out-Null
foreach ($d in "harness", "gpu", "lua") { Copy-Item -Recurse (Join-Path $root $d) (Join-Path $rel "source\$d") }
Copy-Item (Join-Path $root "setup.ps1") $rel
$Version | Set-Content (Join-Path $rel "version.txt")   # the in-app updater compares this with GitHub

# 3. emulator + force-feedback runtime (SDL2, loaded at run time by vunit.exe)
Copy-Item $vunit (Join-Path $rel "vunit.exe")
if (Test-Path (Join-Path $vdir "SDL2.dll")) { Copy-Item (Join-Path $vdir "SDL2.dll") $rel }
else { throw "SDL2.dll not found beside vunit.exe - the release would ship without force feedback" }
Copy-Item (Join-Path $root "third_party\SDL2-LICENSE.txt") (Join-Path $rel "SDL2-LICENSE.txt")
# MAME's bgfx shader/chain files: used by the Exotica fallback path (MIDZ_GL=0
# -> video bgfx + crt-geom-deluxe). Beside vunit.exe in dev; in the CI clone.
if (Test-Path (Join-Path $vdir "bgfx")) {
    Copy-Item -Recurse (Join-Path $vdir "bgfx") (Join-Path $rel "bgfx")
} else { Write-Host "  [!] bgfx\ not found beside vunit.exe (Exotica fallback CRT unavailable)" -ForegroundColor Yellow }
@"
CRUIS'N COLLECTION
==================
1. Double-click CruisnSetup.exe and add your own ROM zips (MAME 0.286
   sets: crusnusa, crusnwld + crusnwld24, offroadc, crusnexo, plus the
   DSP boot-ROM sets tms320c31 / tms320c32 - older romsets call them
   tms32031 / tms32032, same files). Any filename works - files are
   identified by their contents. The window also health-checks the
   emulator and force feedback.
2. Hit "Launch Collection" (or double-click CruisnCollection.exe).
3. Have a wheel? SETTINGS > CONTROLS SETUP binds it in a minute; force
   feedback then goes to that wheel automatically (SETTINGS > FFB STRENGTH).

In-game: 5 = coin, 1 = start, Esc = menu (resume / CRT / exit),
F9 = CRT toggle, F12 = quit to the launcher, Shift+F12 = quit to the
desktop.
Frontends / shortcuts: "CruisnCollection.exe --game usa" (or world,
offroad, exotica) starts that game with no launcher screen.
Full guide (wheel, force feedback, steering feel, troubleshooting):
docs\INSTALL.md.

This package contains no ROMs. Emulator: MAME (GPL-2.0+), patch series
in patch\, launcher source in source\. SDL2 (zlib license, SDL2-LICENSE.txt)
for wheel force feedback.
"@ | Set-Content (Join-Path $rel "README.txt")

# 5. zip
$stamp = Get-Date -Format "yyyy-MM-dd"
$zip = Join-Path $root "build\CruisnCollection-$stamp.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path $rel -DestinationPath $zip
$mb = [math]::Round((Get-Item $zip).Length / 1MB, 0)
Write-Host "release: $rel" -ForegroundColor Green
Write-Host "zip:     $zip ($mb MB)" -ForegroundColor Green
