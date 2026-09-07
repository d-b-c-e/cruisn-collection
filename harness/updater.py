"""In-app updates from GitHub Releases (public repository: no credentials).

Flow: check() -> newer tag? -> download() the zip -> apply() writes a
PowerShell script that waits for the launcher/setup processes to exit,
unzips over the install folder (rig/ and roms/ untouched - the zip has
neither) and relaunches. The caller exits right after apply().
"""
import json
import hashlib
import os
from pathlib import PurePosixPath
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile

import run_rig

REPO = "d-b-c-e/cruisn-collection"
API = f"https://api.github.com/repos/{REPO}/releases/latest"
UA = "CruisnCollection-updater"


def frozen():
    return bool(getattr(sys, "frozen", False))


def app_dir():
    """The install folder (where CruisnCollection.exe, vunit.exe live)."""
    if frozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    return run_rig.POC


def current_version():
    """'v0.3.4' from version.txt (written by make_release.ps1 -Version),
    'dev' when running from source / an unstamped build."""
    for d in (app_dir(), run_rig.POC):
        try:
            with open(os.path.join(d, "version.txt"), encoding="utf-8") as f:
                v = f.read().strip()
            if v:
                return v
        except OSError:
            pass
    return "dev"


def version_tuple(tag):
    m = re.search(r"v?(\d+)\.(\d+)\.(\d+)", tag or "")
    return tuple(int(x) for x in m.groups()) if m else None


def is_newer(tag, current=None):
    current = current or current_version()
    a, b = version_tuple(tag), version_tuple(current)
    # GitHub's latest endpoint returns stable releases. An installed RC of
    # that same version must still be offered the final release.
    return bool(a and b and (a > b or (a == b and '-' in current and '-' not in tag)))


def _request(url, accept="application/vnd.github+json"):
    h = {"Accept": accept, "User-Agent": UA,
         "X-GitHub-Api-Version": "2022-11-28"}
    tok = os.environ.get("CRUISN_GH_TOKEN")   # developers only (rate limit)
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return urllib.request.Request(url, headers=h)


def check():
    """{'tag', 'name', 'url', 'size', 'notes', 'newer'} for the latest
    release. Raises RuntimeError with a message fit for the screen."""
    try:
        with urllib.request.urlopen(_request(API), timeout=20) as r:
            rel = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError("no release found on GitHub (private "
                               "repository or no release yet)")
        if e.code == 403:
            raise RuntimeError("GitHub is rate-limiting this address - "
                               "try again in an hour")
        raise RuntimeError(f"GitHub error {e.code}")
    except (urllib.error.URLError, OSError) as e:
        raise RuntimeError(f"no connection to GitHub ({getattr(e, 'reason', e)})")
    assets = [a for a in rel.get("assets", [])
              if a.get("name", "").lower().endswith(".zip")]
    if not assets:
        raise RuntimeError("the latest release has no zip attached")
    a = assets[0]
    tag = rel.get("tag_name", "")
    return {"tag": tag, "name": a["name"],
            "url": a["browser_download_url"],
            "size": int(a.get("size", 0)), "notes": rel.get("body", ""),
            "newer": is_newer(tag)}


def download(info, dest_dir=None, progress=None):
    """Fetch the release zip to rig/update/<name>. progress(done, total)."""
    dest_dir = dest_dir or os.path.join(run_rig.POC, "rig", "update")
    if not re.fullmatch(r'[A-Za-z0-9._-]+\.zip', info['name'], re.IGNORECASE):
        raise RuntimeError('release ZIP has an invalid filename')
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, info["name"])
    try:
        body = urllib.request.urlopen(urllib.request.Request(
            info["url"], headers={"User-Agent": UA}), timeout=60)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"download refused ({e.code})")
    except (urllib.error.URLError, OSError) as e:
        raise RuntimeError(f"download failed ({getattr(e, 'reason', e)})")
    total = info.get("size") or 0
    done = 0
    tmp = dest + ".part"
    with body, open(tmp, "wb") as f:
        while True:
            chunk = body.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if progress:
                progress(done, total)
    if total and done != total:
        os.remove(tmp)
        raise RuntimeError(f"download incomplete ({done} of {total} bytes)")
    os.replace(tmp, dest)
    return dest


def validate_update_package(path):
    """Reject partial/wrong archives before any installed file is changed."""
    with zipfile.ZipFile(path) as archive:
        roots=set(); files=set()
        for info in archive.infolist():
            name=info.filename.replace('\\','/')
            parts=PurePosixPath(name).parts
            if not parts or name.startswith('/') or ':' in name or '..' in parts:
                raise ValueError('unsafe update ZIP path')
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('update ZIP contains a symbolic link')
            roots.add(parts[0])
            if info.is_dir():continue
            relative='/'.join(parts[1:]).lower()
            if not relative or relative in files:raise ValueError('duplicate or unrooted update file')
            if relative.startswith(('rig/','roms/')):raise ValueError('update ZIP contains personal runtime data')
            files.add(relative)
        if len(roots)!=1 or not {'cruisncollection.exe','cruisnsetup.exe','vunit.exe','sdl2.dll','version.txt'} <= files:
            raise ValueError('update ZIP is missing required runtime files')
        bad=archive.testzip()
        if bad:raise ValueError(f'update ZIP failed CRC validation: {bad}')
        return next(iter(roots))


def ps_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def apply(zip_path, relaunch=True):
    """Write rig/update/apply.ps1 and start it detached; it waits for
    every process running from the install folder to exit, expands the
    zip over the folder (rig/ and roms/ are not in the zip, so they stay)
    and relaunches the launcher. Caller must exit promptly."""
    if not frozen():
        raise RuntimeError("running from source - update with git pull")
    zip_path=os.path.abspath(zip_path)
    package_root=validate_update_package(zip_path)
    with open(zip_path,'rb') as payload:
        package_hash=hashlib.file_digest(payload,'sha256').hexdigest()
    app = app_dir()
    workdir = os.path.join(run_rig.POC, "rig", "update")
    os.makedirs(workdir, exist_ok=True)
    script = os.path.join(workdir, "apply.ps1")
    log = os.path.join(workdir, "apply.log")
    exe = os.path.join(app, "CruisnCollection.exe")
    extract=tempfile.mkdtemp(prefix='extract-',dir=workdir)
    lines = [
        "$ErrorActionPreference = 'Stop'",
        f"$app = {ps_literal(app)}",
        f"$zip = {ps_literal(zip_path)}",
        f"$log = {ps_literal(log)}",
        f"$extract = {ps_literal(extract)}",
        f"$work = {ps_literal(workdir)}",
        f"$packageRoot = {ps_literal(package_root)}",
        f"$packageHash = {ps_literal(package_hash)}",
        f"$relaunch = ${'true' if relaunch else 'false'}",
        f"$exe = {ps_literal(exe)}",
        "function Log($m) { \"$(Get-Date -Format s)  $m\" | Add-Content $log }",
        "try {",
        "$app = (Resolve-Path -LiteralPath $app).Path",
        "$work = (Resolve-Path -LiteralPath $work).Path",
        "$appPrefix = [IO.Path]::GetFullPath($app).TrimEnd('\\') + '\\'",
        "Log \"update: waiting for the launcher to close\"",
        "$deadline = (Get-Date).AddSeconds(120)",
        "do {",
        "  $busy = Get-Process -ErrorAction SilentlyContinue | Where-Object {",
        "    $_.Path -and $_.Path.StartsWith($appPrefix, 'OrdinalIgnoreCase') -and $_.Id -ne $PID }",
        "  if ($busy) { Start-Sleep -Milliseconds 500 }",
        "} while ($busy -and (Get-Date) -lt $deadline)",
        "if ($busy) { Log \"still running: $($busy.Name -join ', ') - giving up\"; exit 1 }",
        "if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant() -ne $packageHash) { throw 'ZIP changed after validation' }",
        "Log \"expanding $zip\"",
        "Expand-Archive -LiteralPath $zip -DestinationPath $extract -Force",
        "$src = Get-Item -LiteralPath (Join-Path $extract $packageRoot)",
        "if (-not (Test-Path (Join-Path $src.FullName 'CruisnCollection.exe'))) { Log 'zip has no CruisnCollection.exe - aborting'; exit 1 }",
        "Log \"copying $($src.FullName) -> $app\"",
        "robocopy $src.FullName $app /E /XD rig roms /R:5 /W:2 /NFL /NDL /NJH /NJS /NP | Out-Null",
        "if ($LASTEXITCODE -ge 8) { Log \"robocopy failed ($LASTEXITCODE)\"; exit 1 }",
        "$allowed = $work.TrimEnd('\\') + '\\'",
        "$resolved = (Resolve-Path -LiteralPath $extract).Path",
        "if (-not $resolved.StartsWith($allowed, 'OrdinalIgnoreCase') -or ((Get-Item -LiteralPath $resolved).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Refusing cleanup outside update workspace' }",
        "Remove-Item -LiteralPath $resolved -Recurse -Force",
        "Log 'update applied'",
        "if ($relaunch -and (Test-Path $exe)) { Start-Process -FilePath $exe -WorkingDirectory $app -WindowStyle Hidden }",
        "} catch { Log \"update failed: $_\"; exit 1 }",
    ]
    with open(script, "w", encoding="utf-8") as f:
        f.write(chr(10).join(lines) + chr(10))
    try:
        os.remove(log)
    except OSError:
        pass
    # CREATE_NO_WINDOW (a DETACHED powershell never runs: no console host)
    # + NEW_PROCESS_GROUP; the child outlives our exit.
    creationflags = 0x08000000 | 0x00000200
    # A launcher started from PowerShell 7 can inherit its module search path;
    # Windows PowerShell then loses Get-FileHash/Expand-Archive. Let it initialize
    # its own module path, as it does when launched from Explorer.
    helper_env = {key: value for key, value in os.environ.items() if key.upper() != 'PSMODULEPATH'}
    powershell = os.path.join(os.environ['SystemRoot'], 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
    subprocess.Popen(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-WindowStyle", "Hidden", "-File", script],
        creationflags=creationflags, close_fds=True, env=helper_env,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    return script


def status_row():
    """(ok, detail) for the setup window's version row."""
    v = current_version()
    if not frozen():
        return True, f"{v} (running from source)"
    return True, f"{v} - Updates... checks GitHub for a newer release"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--download", action="store_true")
    args = ap.parse_args()
    print("current:", current_version())
    info = check()
    print("latest: ", info["tag"], info["name"], f"{info['size'] / 1e6:.1f} MB",
          "NEWER" if info["newer"] else "not newer")
    if args.download:
        marks = set()

        def prog(d, t):
            pct = int(d * 10 / t) * 10 if t else 0
            if pct not in marks:
                marks.add(pct)
                print(f"  {pct}%", end="", flush=True)
        dest = download(info, progress=prog)
        print()
        print("->", dest, os.path.getsize(dest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
