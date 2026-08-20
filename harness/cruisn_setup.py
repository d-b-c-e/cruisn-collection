"""Cruis'n Collection Setup - friendly GUI installer for ROMs + health check.

Identifies any zip the user hands us by MEMBER names + CRCs against
roms_manifest.json (generated from vunit.exe itself) - filename-independent,
clone-aware, reports exactly what's missing or mismatched, and installs
under the correct set name. Also checks the emulator and FFB plugin.

GUI:    python harness/cruisn_setup.py          (or frozen CruisnSetup.exe)
CLI:    python harness/cruisn_setup.py --check somefile.zip   (JSON verdict)
"""
import json
import os
import shutil
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_rig  # noqa: E402  (POC/VUNIT/ROMPATH resolution, frozen-aware)

GAMES = [("crusnusa", "Cruis'n USA"), ("crusnwld", "Cruis'n World"),
         ("offroadc", "Off Road Challenge"), ("crusnexo", "Cruis'n Exotica")]
FFB_FILES = ["dinput8.dll", "SDL2.dll", "MAME64.dll", "FFBPlugin.ini"]


def manifest_path():
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "roms_manifest.json")


def load_manifest():
    with open(manifest_path()) as f:
        return json.load(f)


def identify(zpath, manifest):
    """Best-effort identification of a zip against every known set.

    Returns dict: set, desc, parent(bool), coverage, crc_ok, missing[],
    bad_crc[], or {'set': None, 'error': ...} when unidentifiable."""
    try:
        with zipfile.ZipFile(zpath) as z:
            members = {i.filename.rsplit("/", 1)[-1].lower():
                       (i.file_size, i.CRC & 0xFFFFFFFF)
                       for i in z.infolist() if not i.is_dir()}
    except (zipfile.BadZipFile, OSError) as e:
        return {"set": None, "error": f"not a readable zip: {e}"}
    if not members:
        return {"set": None, "error": "zip is empty"}

    best = None
    for setname, info in manifest.items():
        expected = {n.lower(): (r["size"], int(r["crc"], 16))
                    for n, r in info["roms"].items()}
        present = [n for n in expected if n in members]
        if not present:
            continue
        crc_ok = sum(1 for n in present if members[n][1] == expected[n][1])
        cand = {
            "set": setname, "desc": info["desc"], "parent": info["parent"],
            "coverage": len(present) / len(expected),
            "crc_ok": crc_ok / len(expected),
            "missing": sorted(n for n in expected if n not in members),
            "bad_crc": sorted(n for n in present
                              if members[n][1] != expected[n][1]),
        }
        key = (cand["coverage"], cand["crc_ok"], cand["parent"])
        if best is None or key > (best["coverage"], best["crc_ok"],
                                  best["parent"]):
            best = cand
    if best is None:
        return {"set": None,
                "error": "no Cruis'n / Off Road Challenge ROMs recognized "
                         "in this file"}
    return best


def verdict_text(v, src):
    name = os.path.basename(src)
    if v["set"] is None:
        return f"{name}: {v['error']}"
    lines = [f"{name}: identified as {v['desc']} [{v['set']}] "
             f"({v['coverage']:.0%} of files present, "
             f"{v['crc_ok']:.0%} checksums match)"]
    if not v["parent"]:
        parent = v["set"].rstrip("0123456789ab")
        lines.append(f"  This is an alternate version - the collection runs "
                     f"the parent set [{parent}]. This file will NOT work; "
                     f"you need the {parent} romset.")
    if v["missing"]:
        show = ", ".join(v["missing"][:5])
        more = f" (+{len(v['missing']) - 5} more)" if len(v["missing"]) > 5 else ""
        lines.append(f"  missing files: {show}{more}")
    if v["bad_crc"]:
        lines.append(f"  {len(v['bad_crc'])} file(s) have unexpected "
                     f"checksums - the game may still run")
    return "\n".join(lines)


def install(zpath, v):
    """Copy an identified parent zip into the rompath under its set name."""
    os.makedirs(run_rig.ROMPATH, exist_ok=True)
    dst = os.path.join(run_rig.ROMPATH, v["set"] + ".zip")
    shutil.copy2(zpath, dst)
    return dst


def game_status(manifest):
    """[(rom, title, state, detail)] - state: ok | issues | missing"""
    out = []
    for rom, title in GAMES:
        found = None
        for ext in (".zip", ".7z"):
            p = os.path.join(run_rig.ROMPATH, rom + ext)
            if os.path.isfile(p):
                found = p
                break
        if not found:
            out.append((rom, title, "missing", "no ROM installed"))
        elif found.endswith(".7z"):
            out.append((rom, title, "ok", "installed (.7z, not verified)"))
        else:
            v = identify(found, manifest)
            if v["set"] == rom and not v["missing"]:
                d = "installed and verified" if not v["bad_crc"] else \
                    f"installed ({len(v['bad_crc'])} checksum oddities)"
                out.append((rom, title, "ok", d))
            elif v["set"] == rom:
                out.append((rom, title, "issues",
                            f"{len(v['missing'])} files missing"))
            else:
                out.append((rom, title, "issues",
                            "file does not look like this game"))
    return out


def env_status():
    rows = []
    ok = os.path.isfile(run_rig.VUNIT)
    rows.append(("emulator (vunit.exe)", ok,
                 run_rig.VUNIT if ok else "not found"))
    vdir = os.path.dirname(run_rig.VUNIT)
    missing = [f for f in FFB_FILES
               if not os.path.isfile(os.path.join(vdir, f))]
    rows.append(("force feedback plugin", not missing,
                 "present" if not missing else "missing: " + ", ".join(missing)))
    return rows


# ---------------------------------------------------------------------------
def run_gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    manifest = load_manifest()
    BG, FG, ACC = "#14101f", "#e8e0d0", "#ffb020"
    root = tk.Tk()
    root.title("Cruis'n Collection Setup")
    root.configure(bg=BG)
    root.geometry("760x560")

    tk.Label(root, text="CRUIS'N  COLLECTION  SETUP", bg=BG, fg=ACC,
             font=("Bahnschrift", 20, "bold")).pack(pady=(16, 8))

    frame = tk.Frame(root, bg=BG)
    frame.pack(fill="x", padx=24)
    rows = {}
    r = 0
    for rom, title in GAMES:
        dot = tk.Label(frame, text="?", width=2, bg=BG, font=("Consolas", 13))
        dot.grid(row=r, column=0, sticky="w")
        tk.Label(frame, text=title, bg=BG, fg=FG, width=22, anchor="w",
                 font=("Bahnschrift", 12)).grid(row=r, column=1, sticky="w")
        det = tk.Label(frame, text="", bg=BG, fg="#9a92a8", anchor="w",
                       font=("Bahnschrift", 10))
        det.grid(row=r, column=2, sticky="w")
        rows[rom] = (dot, det)
        r += 1
    envrows = []
    for label, _, _ in env_status():
        dot = tk.Label(frame, text="?", width=2, bg=BG, font=("Consolas", 13))
        dot.grid(row=r, column=0, sticky="w")
        tk.Label(frame, text=label, bg=BG, fg=FG, width=22, anchor="w",
                 font=("Bahnschrift", 12)).grid(row=r, column=1, sticky="w")
        det = tk.Label(frame, text="", bg=BG, fg="#9a92a8", anchor="w",
                       font=("Bahnschrift", 10))
        det.grid(row=r, column=2, sticky="w")
        envrows.append((dot, det))
        r += 1

    log = tk.Text(root, height=10, bg="#1d1830", fg=FG, wrap="word",
                  font=("Consolas", 9), state="disabled", borderwidth=0)
    log.pack(fill="both", expand=True, padx=24, pady=12)

    def say(msg):
        log.configure(state="normal")
        log.insert("end", msg + "\n")
        log.see("end")
        log.configure(state="disabled")

    def refresh():
        for rom, title, state, detail in game_status(manifest):
            dot, det = rows[rom]
            dot.configure(text={"ok": "●", "issues": "!",
                                "missing": "○"}[state],
                          fg={"ok": "#50d878", "issues": ACC,
                              "missing": "#666078"}[state])
            det.configure(text=detail)
        for (dot, det), (label, ok, detail) in zip(envrows, env_status()):
            dot.configure(text="●" if ok else "!",
                          fg="#50d878" if ok else ACC)
            det.configure(text=detail)

    def add_roms():
        paths = filedialog.askopenfilenames(
            title="Select ROM zip file(s)",
            filetypes=[("zip files", "*.zip"), ("all files", "*.*")])
        for p in paths:
            v = identify(p, manifest)
            say(verdict_text(v, p))
            if v.get("set") and v["parent"]:
                if v["missing"]:
                    if not messagebox.askyesno(
                            "Incomplete set",
                            f"{os.path.basename(p)} is missing "
                            f"{len(v['missing'])} file(s) - the game will "
                            f"likely fail to start.\n\nInstall anyway?"):
                        say("  skipped.")
                        continue
                dst = install(p, v)
                say(f"  installed -> {dst}")
        refresh()

    def launch():
        exe = os.path.join(run_rig.POC, "CruisnCollection.exe")
        if os.path.isfile(exe):
            import subprocess
            subprocess.Popen([exe], cwd=run_rig.POC)
            root.destroy()
        else:
            messagebox.showinfo("Launch", "CruisnCollection.exe not found "
                                "beside this setup (dev checkout? use "
                                "python harness/collection.py)")

    btns = tk.Frame(root, bg=BG)
    btns.pack(pady=(0, 16))
    style = dict(bg="#2a2344", fg=FG, activebackground="#3a3060",
                 activeforeground=FG, font=("Bahnschrift", 11), bd=0,
                 padx=14, pady=6)
    def support():
        import threading

        def work():
            try:
                import support_bundle
                say("building support bundle - a game window will appear "
                    "for ~10 seconds...")
                out = support_bundle.bundle(progress=say)
                say(f"Attach {os.path.basename(out)} to your bug report.")
            except Exception as e:
                say(f"support bundle failed: {e}")

        threading.Thread(target=work, daemon=True).start()

    tk.Button(btns, text="Add ROM file(s)...", command=add_roms,
              **style).pack(side="left", padx=6)
    tk.Button(btns, text="Open ROMs folder",
              command=lambda: os.startfile(run_rig.ROMPATH)
              if os.path.isdir(run_rig.ROMPATH)
              else os.makedirs(run_rig.ROMPATH) or os.startfile(run_rig.ROMPATH),
              **style).pack(side="left", padx=6)
    tk.Button(btns, text="Save support bundle", command=support,
              **style).pack(side="left", padx=6)
    tk.Button(btns, text="Launch Collection", command=launch,
              **style).pack(side="left", padx=6)

    say("Add your own ROM zips - any filename works, they are identified "
        "by their contents.")
    refresh()
    root.mainloop()


def main():
    if "--check" in sys.argv:
        manifest = load_manifest()
        for p in sys.argv[sys.argv.index("--check") + 1:]:
            v = identify(p, manifest)
            v["file"] = p
            print(json.dumps(v, indent=1))
        return 0
    run_gui()
    return 0


if __name__ == "__main__":
    sys.exit(main())
