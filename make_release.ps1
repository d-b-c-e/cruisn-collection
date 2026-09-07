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
if ($Version -notmatch '^(dev|v[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?)$') {
    throw "Version must be dev or vMAJOR.MINOR.PATCH with an optional prerelease suffix"
}
$vunit  = if ($env:CRUISN_VUNIT) { $env:CRUISN_VUNIT } else { "E:\Source\mame-src\vunit.exe" }
$vdir   = Split-Path $vunit
$dist   = Join-Path $root "build\dist\CruisnCollection"
$rel    = Join-Path $root "build\release\CruisnCollection"

function Remove-BuildDirectory([string]$Path) {
    $buildRoot = [IO.Path]::GetFullPath((Join-Path $root 'build')) + [IO.Path]::DirectorySeparatorChar
    $target = [IO.Path]::GetFullPath($Path)
    if (-not $target.StartsWith($buildRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing deletion outside build directory: $target"
    }
    if (Test-Path -LiteralPath $target) {
        $resolved = (Resolve-Path -LiteralPath $target).Path
        if (-not $resolved.StartsWith($buildRoot, [StringComparison]::OrdinalIgnoreCase) -or
            ((Get-Item -LiteralPath $target).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Refusing redirected build directory: $resolved"
        }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}

function Copy-TrackedTree([string]$Tree, [string]$Destination) {
    $files = & git -C $root ls-files -- $Tree
    if ($LASTEXITCODE -ne 0 -or -not $files) { throw "Cannot enumerate source tree $Tree" }
    foreach ($file in $files) {
        $dst = Join-Path $Destination $file
        New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null
        Copy-Item -LiteralPath (Join-Path $root $file) -Destination $dst
    }
}

Write-Host "== building release ==" -ForegroundColor Cyan

# 1. frozen shell + setup GUI - ALWAYS re-frozen: a stale build\dist from
# an earlier session silently shipped a month-old launcher once
$glfwdll = & python -c "import glfw.library; print(glfw.library.glfw._name)"
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $glfwdll)) { throw "GLFW dependency lookup failed" }
foreach ($stale in (Join-Path $root "build\dist"), (Join-Path $root "build\work")) {
    Remove-BuildDirectory $stale
}
if (-not (Test-Path (Join-Path $dist "CruisnCollection.exe"))) {
    Write-Host "  freezing shell (PyInstaller)..."
    & python -m PyInstaller --noconfirm --onedir --noconsole --name CruisnCollection `
        --add-binary "$glfwdll;glfw" `
        --distpath (Join-Path $root "build\dist") --workpath (Join-Path $root "build\work") `
        --specpath (Join-Path $root "build") (Join-Path $root "harness\collection.py") | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Launcher freezing failed ($LASTEXITCODE)" }
}
if (-not (Test-Path (Join-Path $root "build\dist\CruisnSetup.exe"))) {
    Write-Host "  freezing setup GUI (PyInstaller onefile)..."
    & python -m PyInstaller --noconfirm --onefile --noconsole --name CruisnSetup `
        --add-data "$(Join-Path $root 'harness\roms_manifest.json');." `
        --add-data "$(Join-Path $root 'lua\input_dump.lua');." `
        --hidden-import support_bundle --hidden-import dinput_axes `
        --distpath (Join-Path $root "build\dist") --workpath (Join-Path $root "build\work") `
        --specpath (Join-Path $root "build") (Join-Path $root "harness\cruisn_setup.py") | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Setup freezing failed ($LASTEXITCODE)" }
}

# 2. layout
Remove-BuildDirectory $rel
New-Item -ItemType Directory -Force $rel | Out-Null
Copy-Item -Recurse (Join-Path $dist "*") $rel
Copy-Item (Join-Path $root "build\dist\CruisnSetup.exe") $rel
foreach ($d in "fixtures", "patch", "docs") { Copy-TrackedTree $d $rel }
# The toolkit's force profiles. run_rig.deploy_force_profiles() copies this
# beside vunit.exe at every launch (backing up an edited one first), so the
# SETTINGS > FORCE FEEDBACK > FEEL row has real tunes to offer. Without it the
# emulator falls back to values equal to cruisn-vunit@1 and FEEL has one entry.
New-Item -ItemType Directory -Force (Join-Path $rel "lib\toolkit\profiles") | Out-Null
Copy-Item (Join-Path $root "lib\toolkit\profiles\force-profiles.ini") (Join-Path $rel "lib\toolkit\profiles")
# ...and beside vunit.exe, where the emulator reads it and where anyone
# looking for the tunes will look. Without this the four shipped tunes are
# invisible until the first launch deploys them.
Copy-Item (Join-Path $root "lib\toolkit\profiles\force-profiles.ini") $rel
Copy-Item (Join-Path $root "lib\toolkit\VERSION") (Join-Path $rel "lib\toolkit")
# The starter file for a player's own tune, beside vunit.exe next to the tunes
# it extends. One copy only: a second buried one just raises the question of
# which is real. Inert until renamed to force-profiles.user.ini.
Copy-Item (Join-Path $root "profiles\force-profiles.user.ini.example") $rel
New-Item -ItemType Directory -Force (Join-Path $rel "roms") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $rel "source") | Out-Null
foreach ($d in "harness", "gpu", "lua", "native", "lib", "profiles") { Copy-TrackedTree $d (Join-Path $rel "source") }
foreach ($f in "make_release.ps1", "setup.ps1") { Copy-Item (Join-Path $root $f) (Join-Path $rel "source") }
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
} else { throw "bgfx\ missing beside vunit.exe; Exotica fallback CRT would be unavailable" }

# 4. Explicit repository media only. Never package the development rig or
# copy personal settings/calibration as a side effect of bundling menu music.
if (-not $NoMedia) {
    Copy-Item -Recurse (Join-Path $root 'media\art') (Join-Path $rel 'art')
    New-Item -ItemType Directory -Force (Join-Path $rel 'audio') | Out-Null
    Copy-Item (Join-Path $root 'media\menumusic.mp3') (Join-Path $rel 'audio')
}
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
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$zip = Join-Path $root "build\CruisnCollection-$Version-$stamp.zip"
if (Test-Path -LiteralPath $zip) { throw "Package already exists: $zip" }
Compress-Archive -Path $rel -DestinationPath $zip
$options = if ($NoMedia) { @('--no-media') } else { @() }
& python (Join-Path $root 'harness\check_release_package.py') $zip --candidate $vunit `
    --report "$zip.check.json" --write-manifest "$zip.manifest.json" @options
if ($LASTEXITCODE -ne 0) { throw "Packaged release validation failed" }
$mb = [math]::Round((Get-Item $zip).Length / 1MB, 0)
Write-Host "release: $rel" -ForegroundColor Green
Write-Host "zip:     $zip ($mb MB)" -ForegroundColor Green
