"""Vendor a committed toolkit source tag with local-edit checks and a manifest.

Updates the collection's library and MAME's header copies together. Commits and
rebuilding remain explicit. Runtime user profiles beside vunit.exe are untouched.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from verification import write_json

ROOT = Path(__file__).resolve().parents[1]
FILES = {"LICENSE": "LICENSE",
         "include/force_model.h": "native/forcemodel/force_model.h",
         "include/force_profile.h": "native/forcemodel/force_profile.h",
         "include/impact_mixer.h": "native/forcemodel/impact_mixer.h",
         "include/signal_sample.h": "native/telemetry/signal_sample.h",
         "profiles/force-profiles.ini": "profiles/force-profiles.ini"}


def blob(repo, ref, path):
    return subprocess.check_output(["git", "-C", str(repo), "show", f"{ref}:{path}"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, default=Path(r"E:\Source\dbce-wheel-mod-toolkit"))
    ap.add_argument("--mame", type=Path, default=Path(r"E:\Source\mame-src"))
    ap.add_argument("--ref", required=True, help="published source tag")
    ap.add_argument("--previous-ref", help="explicit historical source for bootstrapping a stale pin")
    ap.add_argument("--write", action="store_true", help="apply changes after checking local edits")
    args = ap.parse_args(argv)
    library = ROOT / "lib" / "toolkit"
    previous = args.previous_ref or (library / "VERSION").read_text().splitlines()[0]
    source_commit = subprocess.check_output(["git", "-C", str(args.source), "rev-parse",
                                             args.ref + "^{commit}"], text=True).strip()
    pending = []
    hashes = {}
    for relative, original in FILES.items():
        expected = blob(args.source, args.ref, original)
        hashes[relative] = hashlib.sha256(expected).hexdigest()
        exists = subprocess.run(["git", "-C", str(args.source), "cat-file", "-e",
                                 f"{previous}:{original}"], capture_output=True)
        if exists.returncode and subprocess.run(["git", "-C", str(args.source),
                "rev-parse", "--verify", previous + "^{commit}"], capture_output=True).returncode:
            raise ValueError(f"previous toolkit ref does not resolve: {previous}")
        old = blob(args.source, previous, original) if exists.returncode == 0 else None
        targets = [library / relative]
        if relative.startswith("include/"):
            targets.append(args.mame / "src" / "mame" / "midway" / "dbce" / Path(relative).name)
        for target in targets:
            current = target.read_bytes().replace(b"\r\n", b"\n") if target.exists() else None
            if current is not None and current not in (old, expected):
                raise ValueError(f"locally edited or unrecognized copy, refusing overwrite: {target}")
            if current != expected:
                pending.append((target, expected))
    version = f"{args.ref}\n{source_commit}\n".encode("utf-8")
    for target in (library / "VERSION", args.mame / "src" / "mame" / "midway" / "dbce" / "VERSION"):
        current = target.read_bytes().replace(b"\r\n", b"\n") if target.exists() else None
        if current != version:
            pending.append((target, version))
    manifest = {"schema": 1, "ref": args.ref, "commit": source_commit, "files": hashes}
    manifest_path = library / "MANIFEST.json"
    manifest_matches = manifest_path.exists() and json.loads(manifest_path.read_text()) == manifest
    for target, _ in pending:
        print(f"update: {target}")
    if args.write:
        for target, expected in pending:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(expected)
        write_json(manifest_path, manifest)
        print("copied committed sources; rebuild and commit MAME, then refresh its exported patch")
    if not manifest_matches:
        print(f"update: {manifest_path}")
    if not pending and manifest_matches:
        print("toolkit sources, version markers and manifest match the committed ref")
    return 1 if (pending or not manifest_matches) and not args.write else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"sync failed: {exc}", file=sys.stderr)
        sys.exit(1)
