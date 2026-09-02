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
#   - FFB Arcade Plugin files (GPL-3.0, license included, GUID blanked)
#   - NVRAM fixtures, setup.ps1, docs
param([switch]$NoMedia)
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
        --hidden-import support_bundle `
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
# MAME's bgfx shader/chain files: used by the Exotica fallback path (MIDZ_GL=0
# -> video bgfx + crt-geom-deluxe). Beside vunit.exe in dev; in the CI clone.
if (Test-Path (Join-Path $vdir "bgfx")) {
    Copy-Item -Recurse (Join-Path $vdir "bgfx") (Join-Path $rel "bgfx")
} else { Write-Host "  [!] bgfx\ not found beside vunit.exe (Exotica fallback CRT unavailable)" -ForegroundColor Yellow }
if (Test-Path (Join-Path $vdir "FFBPlugin.ini")) {
    # ship the ini configured for MAME-outputs mode, wheel GUID blanked
    (Get-Content (Join-Path $vdir "FFBPlugin.ini")) `
        -replace '^GameId=.*', 'GameId=22' `
        -replace '^DeviceGUID=.*', 'DeviceGUID=' `
        -replace '^Logging=.*', 'Logging=0' `
        -replace '^BeepWhenHook=.*', 'BeepWhenHook=0' |
        Set-Content (Join-Path $rel "FFBPlugin.ini")
}
try {
    Invoke-WebRequest -UseBasicParsing -OutFile (Join-Path $rel "FFBPLUGIN-LICENSE.txt") `
        "https://raw.githubusercontent.com/Boomslangnz/FFBArcadePlugin/master/LICENSE"
} catch {
    "FFB Arcade Plugin by Boomslangnz - GPL-3.0 - https://github.com/Boomslangnz/FFBArcadePlugin" |
        Set-Content (Join-Path $rel "FFBPLUGIN-LICENSE.txt")
}

# 3b. menu art + music (skippable with -NoMedia); repo media/ preferred so
# CI builds work without the LaunchBox library
if (-not $NoMedia) {
    $artsrc = if (Test-Path (Join-Path $root "media\art")) { Join-Path $root "media\art" }
              elseif ($env:CRUISN_ART) { $env:CRUISN_ART }
              else { "E:\Source\launchbox\Launchbox-Racing\Images\Arcade" }
    $artfiles = @(
        "Clear Logo\Cruis_n USA-01.png",
        "Clear Logo\Cruis_n World-01.png",
        "Clear Logo\Off Road Challenge-01.png",
        "Clear Logo\North America\Cruis_n Exotica-01.png",
        "Screenshot - Game Title\Cruis_n USA-01.jpg",
        "Screenshot - Game Title\Cruis_n World-01.png",
        "Screenshot - Game Title\Off Road Challenge-01.png",
        "Screenshot - Game Title\Cruis_n Exotica-02.png")
    foreach ($f in $artfiles) {
        $src = Join-Path $artsrc $f
        if (Test-Path $src) {
            $dst = Join-Path $rel "art\$f"
            New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null
            Copy-Item $src $dst
        } else { Write-Host "  [!] art missing: $f (menu falls back to generated card)" -ForegroundColor Yellow }
    }
    $music = Join-Path $root "media\menumusic.mp3"
    if (-not (Test-Path $music)) { $music = Join-Path $root "rig\assets\menumusic.mp3" }
    if (Test-Path $music) {
        New-Item -ItemType Directory -Force (Join-Path $rel "rig\assets") | Out-Null
        Copy-Item $music (Join-Path $rel "rig\assets\menumusic.mp3")
    } else { Write-Host "  [!] no menumusic.mp3 (menu will be silent; harness\make_music.py builds one)" -ForegroundColor Yellow }
    Write-Host "  media bundled (use -NoMedia for a clean variant)"
}

# 4. README
@"
CRUIS'N COLLECTION
==================
1. Double-click CruisnSetup.exe and add your own ROM zips (MAME 0.286
   sets: crusnusa, crusnwld + crusnwld24, offroadc, crusnexo). Any
   filename works - files are identified by their contents. The window
   also health-checks the emulator and force-feedback plugin.
2. Hit "Launch Collection" (or double-click CruisnCollection.exe).
3. Have a wheel? SETTINGS > CONTROLS SETUP binds it in a minute.

In-game: 5 = coin, 1 = start, Esc = menu (resume / CRT / exit),
F9 = CRT toggle, F12 = instant quit.
Full guide (wheel, force feedback, troubleshooting): docs\INSTALL.md.

This package contains no ROMs. Emulator: MAME (GPL-2.0+), patch series
in patch\, launcher source in source\. FFB Arcade Plugin (c)
Boomslangnz, GPL-3.0 (FFBPLUGIN-LICENSE.txt).
"@ | Set-Content (Join-Path $rel "README.txt")

# 5. zip
$stamp = Get-Date -Format "yyyy-MM-dd"
$zip = Join-Path $root "build\CruisnCollection-$stamp.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path $rel -DestinationPath $zip
$mb = [math]::Round((Get-Item $zip).Length / 1MB, 0)
Write-Host "release: $rel" -ForegroundColor Green
Write-Host "zip:     $zip ($mb MB)" -ForegroundColor Green
