"""Generate roms_manifest.json from vunit.exe -listroms output.

The setup GUI identifies user-supplied zips by their member names/CRCs
against this manifest - filename-independent, clone-aware. Regenerate
whenever the MAME base or the supported set list changes:

    python harness/gen_rom_manifest.py
"""
import json
import os
import re
import subprocess
import sys

POC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VUNIT = os.environ.get("CRUISN_VUNIT", r"E:\Source\mame-src\vunit.exe")
OUT = os.path.join(POC, "harness", "roms_manifest.json")

# parents the launcher can start; clones listed for identification messaging
SETS = {
    "crusnusa": "Cruis'n USA v4.5",
    "crusnusa44": "Cruis'n USA v4.4", "crusnusa41": "Cruis'n USA v4.1",
    "crusnusa40": "Cruis'n USA v4.0", "crusnusa21": "Cruis'n USA v2.1",
    "crusnusa20": "Cruis'n USA v2.0", "crusnusa11": "Cruis'n USA v1.1",
    "crusnwld": "Cruis'n World v2.5",
    "crusnwld24": "Cruis'n World v2.4", "crusnwld23": "Cruis'n World v2.3",
    "crusnwld20": "Cruis'n World v2.0", "crusnwld19": "Cruis'n World v1.9",
    "crusnwld17": "Cruis'n World v1.7", "crusnwld13": "Cruis'n World v1.3",
    "offroadc": "Off Road Challenge v1.63",
    "offroadc5": "Off Road Challenge v1.50",
    "offroadc4": "Off Road Challenge v1.40",
    "offroadc3": "Off Road Challenge v1.30",
    "offroadc1": "Off Road Challenge v1.10",
    "offroadc0": "Off Road Challenge v1.00",
    # DSP boot ROMs - MAME *device* sets every player needs beside the
    # game zips (tiny; part of any full 0.286 romset, easy to miss)
    "tms320c31": "TMS320C31 DSP boot ROM (Cruis'n USA / World / Off Road)",
    "tms320c32": "TMS320C32 DSP boot ROM (Cruis'n Exotica)",
    "crusnexo": "Cruis'n Exotica v2.4",
    "crusnexoa": "Cruis'n Exotica v2.0", "crusnexob": "Cruis'n Exotica v1.6",
    "crusnexoc": "Cruis'n Exotica v1.3", "crusnexod": "Cruis'n Exotica v1.0",
}
PARENTS = {"crusnusa", "crusnwld", "offroadc", "crusnexo",
           "tms320c31", "tms320c32"}

# "BAD CRC(...)" rows are BAD_DUMP entries MAME still requires present
ROW = re.compile(r"^(\S+)\s+(\d+)\s+(?:BAD )?CRC\(([0-9a-f]{8})\)", re.M)


def main():
    manifest = {}
    for setname, desc in SETS.items():
        p = subprocess.run([VUNIT, "-listroms", setname],
                           capture_output=True, text=True,
                           cwd=os.path.dirname(VUNIT))
        roms = {m.group(1): {"size": int(m.group(2)), "crc": m.group(3)}
                for m in ROW.finditer(p.stdout)}
        if not roms:
            print(f"  [!] no roms parsed for {setname} - skipped")
            continue
        manifest[setname] = {
            "desc": desc,
            "parent": setname in PARENTS,
            "roms": roms,
        }
        print(f"  {setname}: {len(roms)} roms")
    # device ROMs (the DSP boot files) are listed under every game that
    # uses the device; they live in their own zips, so strip them from the
    # game sets or a normal split game zip reads as "1 file missing"
    devnames = {n for d in ("tms320c31", "tms320c32") if d in manifest
                for n in manifest[d]["roms"]}
    for setname, info in manifest.items():
        if setname not in ("tms320c31", "tms320c32"):
            for n in devnames:
                info["roms"].pop(n, None)
    with open(OUT, "w") as f:
        json.dump(manifest, f, indent=1)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    sys.exit(main())
