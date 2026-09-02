# Cruis'n Collection - one-time setup / health check.
# Run: right-click -> Run with PowerShell (no admin needed). Re-run any time.
# Works both in a release folder (frozen CruisnCollection.exe beside this
# script) and in the dev checkout (python + harness\collection.py).
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$frozen = Test-Path (Join-Path $root "CruisnCollection.exe")
$script:bad = $false
Write-Host "== Cruis'n Collection setup ==" -ForegroundColor Cyan

function Fail($msg) { Write-Host "  [X] $msg" -ForegroundColor Red; $script:bad = $true }
function Warn($msg) { Write-Host "  [!] $msg" -ForegroundColor Yellow }
function Ok($msg)   { Write-Host "  [ok] $msg" -ForegroundColor Green }

# --- 1. launcher runtime -----------------------------------------------------
if ($frozen) {
    Ok "frozen launcher present (no Python required)"
} else {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { Fail "Python not found - install from python.org (check 'Add to PATH')" }
    else {
        Ok "Python at $($py.Source)"
        Write-Host "  installing/verifying packages (numpy pillow moderngl glfw)..."
        & python -m pip install --quiet numpy pillow moderngl glfw
        Ok "Python packages ready"
    }
}

# --- 2. vunit.exe ------------------------------------------------------------
$vunit = $env:CRUISN_VUNIT
if (-not $vunit) {
    $vunit = Join-Path $root "vunit.exe"
    if (-not (Test-Path $vunit) -and -not $frozen) { $vunit = "E:\Source\mame-src\vunit.exe" }
}
if (-not (Test-Path $vunit)) {
    $ans = Read-Host "Path to vunit.exe (Enter to skip)"
    if ($ans) { $vunit = $ans }
}
if (Test-Path $vunit) { Ok "vunit.exe: $vunit" }
else { Fail "vunit.exe not found - see docs\INSTALL.md (developer section) to build it" }

# --- 3. ROMs -----------------------------------------------------------------
$roms = $env:CRUISN_ROMS
if (-not $roms) { $roms = Join-Path $root "roms" }
if (-not (Test-Path (Join-Path $roms "crusnusa.zip"))) {
    $ans = Read-Host "Directory containing your ROM zips (Enter for $roms)"
    if ($ans) { $roms = $ans }
}
New-Item -ItemType Directory -Force $roms | Out-Null
$have = @(); $miss = @()
foreach ($r in "crusnusa", "crusnwld", "offroadc", "crusnexo") {
    if ((Test-Path (Join-Path $roms "$r.zip")) -or (Test-Path (Join-Path $roms "$r.7z")) -or (Test-Path (Join-Path $roms $r))) { $have += $r } else { $miss += $r }
}
if ($have) { Ok ("ROMs found: " + ($have -join ", ")) }
if ($miss) { Warn "missing ROM sets (those games will not run): $($miss -join ', ')" }
if ($have -contains "crusnwld") {
    $w24 = (Test-Path (Join-Path $roms "crusnwld24.zip")) -or (Test-Path (Join-Path $roms "crusnwld24.7z"))
    if (-not $w24) { Warn "crusnwld24 (World rev 2.4, manual transmission) not found - fine if your crusnwld set is merged; otherwise World runs rev 2.5 (automatic only)" }
}
if (-not $have) { Fail "no ROM sets in $roms - copy your own dumps there and re-run" }

# --- 4. FFB Arcade Plugin (optional but recommended) -------------------------
if (Test-Path $vunit) {
    $vdir = Split-Path $vunit
    $ffb = @("dinput8.dll", "SDL2.dll", "MAME64.dll", "FFBPlugin.ini")
    $missing = @($ffb | Where-Object { -not (Test-Path (Join-Path $vdir $_)) })
    if (-not $missing) { Ok "FFB Arcade Plugin present" }
    else {
        Warn "FFB plugin files missing beside vunit.exe: $($missing -join ', ')"
        $dl = Read-Host "Download the official FFB Arcade Plugin now? ~117 MB (y/N)"
        if ($dl -match '^[yY]') {
            try {
                $api = Invoke-RestMethod "https://api.github.com/repos/Boomslangnz/FFBArcadePlugin/releases/latest"
                $asset = $api.assets | Where-Object { $_.name -like "*.zip" } | Select-Object -First 1
                $tmpz = Join-Path $env:TEMP "ffbplugin.zip"
                $tmpd = Join-Path $env:TEMP "ffbplugin_x"
                Write-Host "  downloading $($asset.name)..."
                Invoke-WebRequest -UseBasicParsing -OutFile $tmpz $asset.browser_download_url
                if (Test-Path $tmpd) { Remove-Item -Recurse -Force $tmpd }
                Expand-Archive $tmpz $tmpd
                $m64 = Get-ChildItem -Recurse -Directory $tmpd | Where-Object { $_.Name -eq "MAME 64bit Outputs" } | Select-Object -First 1
                if ($m64) {
                    foreach ($f in $ffb) {
                        $srcf = Join-Path $m64.FullName $f
                        if ((Test-Path $srcf) -and -not (Test-Path (Join-Path $vdir $f))) {
                            Copy-Item $srcf $vdir
                        }
                    }
                    Ok "FFB plugin installed (edit FFBPlugin.ini: GameId=22; your wheel GUID appears in FFBlog.txt after one run)"
                } else { Warn "MAME64.dll not found in the release archive - install manually" }
                Remove-Item -Force $tmpz -ErrorAction SilentlyContinue
                Remove-Item -Recurse -Force $tmpd -ErrorAction SilentlyContinue
            } catch { Warn "download failed ($_): install manually from github.com/Boomslangnz/FFBArcadePlugin" }
        } else {
            Warn "skipped - wheel force feedback will be inactive (steering still works)"
        }
    }
}

# --- 5. optional menu music --------------------------------------------------
if (-not (Test-Path (Join-Path $root "rig\assets\menumusic.wav"))) {
    Write-Host "  (optional) menu music: any YouTube/audio URL, or Enter to skip"
    $url = Read-Host "  music URL"
    if ($url) {
        $py = Get-Command python -ErrorAction SilentlyContinue
        $mm = Join-Path $root ($(if ($frozen) { "source\harness\make_music.py" } else { "harness\make_music.py" }))
        if ($py -and (Test-Path $mm)) {
            & python -m pip install --quiet yt-dlp
            & python $mm $url
        } else { Warn "music pipeline needs Python + ffmpeg - see docs\INSTALL.md" }
    }
}

# --- 6. write the launcher entry --------------------------------------------
$bat = Join-Path $root "CruisnCollection.bat"
$exeline = if ($frozen) { "start `"`" `"$root\CruisnCollection.exe`" %*" }
           else { "start `"Cruisn Collection`" /min python harness\collection.py %*" }
@"
@echo off
REM generated by setup.ps1 - re-run setup to regenerate
set CRUISN_VUNIT=$vunit
set CRUISN_ROMS=$roms
cd /d "$root"
$exeline
"@ | Set-Content -Encoding ascii $bat
Ok "launcher entry written: $bat"

if ($script:bad) {
    Write-Host "`nSetup finished WITH ISSUES - fix the [X] items above and re-run." -ForegroundColor Yellow
} else {
    Write-Host "`nAll good. Start with CruisnCollection.bat (pin it anywhere)." -ForegroundColor Cyan
}
Read-Host "Press Enter to close"
