"""In-app updates from GitHub Releases.

The repository is private, so every request needs a token the tester
creates once (fine-grained personal access token, read-only Contents on
this one repository - they are collaborators already). It lives in
rig/collection.ini [update] token=, entered through the setup window.

Flow: check() -> newer tag? -> download() the zip -> apply() writes a
PowerShell script that waits for the launcher/setup processes to exit,
unzips over the install folder (rig/ and roms/ untouched - the zip has
neither) and relaunches. The caller exits right after apply().
"""
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

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


def token():
    return run_rig._collection_ini_get("update", "token")


def set_token(tok):
    run_rig._collection_ini_set("update", "token", (tok or "").strip())


def version_tuple(tag):
    m = re.search(r"v?(\d+)\.(\d+)\.(\d+)", tag or "")
    return tuple(int(x) for x in m.groups()) if m else None


def is_newer(tag, current=None):
    a, b = version_tuple(tag), version_tuple(current or current_version())
    return bool(a and b and a > b)


def _request(url, tok, accept="application/vnd.github+json"):
    req = urllib.request.Request(url, headers={
        "Accept": accept, "User-Agent": UA,
        "X-GitHub-Api-Version": "2022-11-28",
        "Authorization": f"Bearer {tok}"})
    return req


def check(tok=None):
    """{'tag', 'name', 'url', 'size', 'notes', 'newer'} for the latest
    release. Raises RuntimeError with a message fit for the screen."""
    tok = tok or token()
    if not tok:
        raise RuntimeError("no GitHub token - enter one in the setup window "
                           "(Updates...)")
    try:
        with urllib.request.urlopen(_request(API, tok), timeout=20) as r:
            rel = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise RuntimeError("GitHub rejected the token (expired?)")
        if e.code in (403, 404):
            raise RuntimeError("no access to the releases - the token needs "
                               "read access to this repository")
        raise RuntimeError(f"GitHub error {e.code}")
    except (urllib.error.URLError, OSError) as e:
        raise RuntimeError(f"no connection to GitHub ({getattr(e, 'reason', e)})")
    assets = [a for a in rel.get("assets", [])
              if a.get("name", "").lower().endswith(".zip")]
    if not assets:
        raise RuntimeError("the latest release has no zip attached")
    a = assets[0]
    tag = rel.get("tag_name", "")
    return {"tag": tag, "name": a["name"], "url": a["url"],
            "size": int(a.get("size", 0)), "notes": rel.get("body", ""),
            "newer": is_newer(tag)}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def download(info, dest_dir=None, progress=None, tok=None):
    """Fetch the release zip to rig/update/<name>. GitHub answers the
    asset URL with a redirect to its CDN, which must NOT see the
    Authorization header (it rejects two credentials) - so take the
    redirect by hand and fetch the CDN URL bare. progress(done, total)."""
    tok = tok or token()
    dest_dir = dest_dir or os.path.join(run_rig.POC, "rig", "update")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, info["name"])
    opener = urllib.request.build_opener(_NoRedirect())
    url = info["url"]
    try:
        with opener.open(_request(url, tok, "application/octet-stream"),
                         timeout=30) as r:
            location = None
            body = r
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            location = e.headers.get("Location")
            body = None
        else:
            raise RuntimeError(f"download refused ({e.code})")
    if location:
        body = urllib.request.urlopen(urllib.request.Request(
            location, headers={"User-Agent": UA}), timeout=60)
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


def apply(zip_path, relaunch=True):
    """Write rig/update/apply.ps1 and start it detached; it waits for
    every process running from the install folder to exit, expands the
    zip over the folder (rig/ and roms/ are not in the zip, so they stay)
    and relaunches the launcher. Caller must exit promptly."""
    if not frozen():
        raise RuntimeError("running from source - update with git pull")
    app = app_dir()
    workdir = os.path.join(run_rig.POC, "rig", "update")
    os.makedirs(workdir, exist_ok=True)
    script = os.path.join(workdir, "apply.ps1")
    log = os.path.join(workdir, "apply.log")
    exe = os.path.join(app, "CruisnCollection.exe")
    lines = [
        "$ErrorActionPreference = 'Continue'",
        f"$app = '{app}'",
        f"$zip = '{zip_path}'",
        f"$log = '{log}'",
        f"$extract = '{os.path.join(workdir, 'extract')}'",
        f"$relaunch = ${'true' if relaunch else 'false'}",
        f"$exe = '{exe}'",
        "function Log($m) { \"$(Get-Date -Format s)  $m\" | Add-Content $log }",
        "Log \"update: waiting for the launcher to close\"",
        "$deadline = (Get-Date).AddSeconds(120)",
        "do {",
        "  $busy = Get-Process -ErrorAction SilentlyContinue | Where-Object {",
        "    $_.Path -and $_.Path.StartsWith($app, 'OrdinalIgnoreCase') -and $_.Id -ne $PID }",
        "  if ($busy) { Start-Sleep -Milliseconds 500 }",
        "} while ($busy -and (Get-Date) -lt $deadline)",
        "if ($busy) { Log \"still running: $($busy.Name -join ', ') - giving up\"; exit 1 }",
        "if (Test-Path $extract) { Remove-Item -Recurse -Force $extract }",
        "Log \"expanding $zip\"",
        "Expand-Archive -LiteralPath $zip -DestinationPath $extract -Force",
        "$src = Get-ChildItem $extract -Directory | Select-Object -First 1",
        "if (-not $src) { $src = Get-Item $extract }",
        "if (-not (Test-Path (Join-Path $src.FullName 'CruisnCollection.exe'))) { Log 'zip has no CruisnCollection.exe - aborting'; exit 1 }",
        "Log \"copying $($src.FullName) -> $app\"",
        "robocopy $src.FullName $app /E /XD rig roms /R:5 /W:2 /NFL /NDL /NJH /NJS /NP | Out-Null",
        "if ($LASTEXITCODE -ge 8) { Log \"robocopy failed ($LASTEXITCODE)\"; exit 1 }",
        "Remove-Item -Recurse -Force $extract -ErrorAction SilentlyContinue",
        "Remove-Item -Force $zip -ErrorAction SilentlyContinue",
        "Log 'update applied'",
        "if ($relaunch -and (Test-Path $exe)) { Start-Process -FilePath $exe -WorkingDirectory $app }",
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
    subprocess.Popen(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-WindowStyle", "Hidden", "-File", script],
        creationflags=creationflags, close_fds=True,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    return script


def status_row():
    """(ok, detail) for the setup window's version row."""
    v = current_version()
    if not frozen():
        return True, f"{v} (running from source)"
    return (bool(token()),
            f"{v} - GitHub token saved" if token()
            else f"{v} - no GitHub token yet (Updates...)")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--token", default=None,
                    help="use this token instead of the saved one (not saved)")
    args = ap.parse_args()
    tok = args.token or os.environ.get("CRUISN_GH_TOKEN") or token()
    print("current:", current_version())
    info = check(tok)
    print("latest: ", info["tag"], info["name"], f"{info['size'] / 1e6:.1f} MB",
          "NEWER" if info["newer"] else "not newer")
    if args.download:
        dest = download(info, tok=tok, progress=lambda d, t: print(
            f"\r  {d / 1e6:.0f}/{t / 1e6:.0f} MB", end=""))
        print("\n->", dest, os.path.getsize(dest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
