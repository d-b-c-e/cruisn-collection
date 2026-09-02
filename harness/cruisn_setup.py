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


_MANIFEST = None


def load_manifest():
    global _MANIFEST
    with open(manifest_path()) as f:
        _MANIFEST = json.load(f)
    return _MANIFEST


def manifest_cache():
    return _MANIFEST if _MANIFEST is not None else load_manifest()


def parent_of(setname, manifest):
    """Parent set name for a clone (crusnwld24 -> crusnwld)."""
    for cand in sorted(manifest, key=len, reverse=True):
        if manifest[cand]["parent"] and setname.startswith(cand):
            return cand
    return setname


def identify(zpath, manifest, want=None):
    """Best-effort identification of a zip against every known set.

    want: evaluate the zip against that one set instead of picking the
    best match (a merged parent zip also fully covers its clones' few
    unique files, and one redumped file would let a clone outscore the
    parent). Returns dict: set, desc, parent(bool), coverage, crc_ok,
    missing[], bad_crc[], or {'set': None, 'error': ...}."""
    try:
        with zipfile.ZipFile(zpath) as z:
            members = {i.filename.rsplit("/", 1)[-1].lower():
                       (i.file_size, i.CRC & 0xFFFFFFFF)
                       for i in z.infolist() if not i.is_dir()}
    except (zipfile.BadZipFile, OSError) as e:
        return {"set": None, "error": f"not a readable zip: {e}"}
    if not members:
        return {"set": None, "error": "zip is empty"}

    member_crcs = {crc for _, crc in members.values()}
    best = None
    for setname, info in manifest.items():
        if want and setname != want:
            continue
        expected = {n.lower(): (r["size"], int(r["crc"], 16))
                    for n, r in info["roms"].items()}
        if not info["parent"]:
            # a clone's own files are only those that differ from its
            # parent (MAME loads the rest from the parent set) - a split
            # crusnwld24.zip legitimately holds just its 4 game ROMs
            parent = parent_of(setname, manifest)
            pexp = {n.lower(): int(r["crc"], 16)
                    for n, r in manifest[parent]["roms"].items()}
            expected = {n: v for n, v in expected.items()
                        if pexp.get(n) != v[1]}
        # MAME matches ROMs by hash, not filename (merged sets nest files
        # under subfolders or rename them): a file counts as present when
        # its name OR its CRC is in the zip
        present = [n for n in expected
                   if n in members or expected[n][1] in member_crcs]
        if not present:
            continue
        crc_ok = sum(1 for n in present
                     if expected[n][1] in member_crcs)
        cand = {
            "set": setname, "desc": info["desc"], "parent": info["parent"],
            "coverage": len(present) / len(expected),
            "crc_ok": crc_ok / len(expected),
            "missing": sorted(n for n in expected if n not in present),
            "bad_crc": sorted(n for n in present
                              if expected[n][1] not in member_crcs),
        }
        # parents outrank clones on equal coverage: a redumped file must
        # not hand the verdict to a 2-file clone
        key = (cand["coverage"], cand["parent"], cand["crc_ok"])
        if best is None or key > (best["coverage"], best["parent"],
                                  best["crc_ok"]):
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
        parent = parent_of(v["set"], manifest_cache())
        if v["set"] == "crusnwld24":
            lines.append("  This is the rev-2.4 set the collection prefers "
                         "for Cruis'n World (it still has the manual "
                         f"transmission). It needs the {parent} set "
                         "installed too.")
        else:
            lines.append(f"  Alternate revision - the collection runs the "
                         f"parent set [{parent}]; this file is not used.")
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
            v = identify(found, manifest, want=rom)
            if v["set"] == rom and not v["missing"]:
                d = "installed and verified" if not v["bad_crc"] else \
                    f"installed ({len(v['bad_crc'])} checksum oddities)"
                if rom == "crusnwld":
                    d += (" - rev 2.4 (manual transmission) available"
                          if run_rig.world24_available()
                          else " - rev 2.4 missing: 2.5 automatic only "
                               "(add crusnwld24.zip)")
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
    c31 = run_rig.boot_rom_available("crusnusa")
    c32 = run_rig.boot_rom_available("crusnexo")
    rows.append(("DSP boot ROMs", c31 and c32,
                 "tms320c31 + tms320c32 present" if (c31 and c32) else
                 "missing: " + ", ".join(
                     n for n, okk in (("tms320c31.zip (USA/World/Off Road)",
                                       c31),
                                      ("tms320c32.zip (Exotica)", c32))
                     if not okk)))
    vdir = os.path.dirname(run_rig.VUNIT)
    missing = [f for f in FFB_FILES
               if not os.path.isfile(os.path.join(vdir, f))]
    rows.append(("force feedback plugin", not missing,
                 "present" if not missing else "missing: " + ", ".join(missing)))
    if not missing:
        guid = run_rig.ffb_device_guid()
        rows.append(("force feedback wheel", bool(guid),
                     f"configured (GUID {guid[:8]}...)" if guid
                     else "not set - use Detect wheel"))
    diag = run_rig.ffb_diag_enabled()
    rows.append(("FFB diagnostics", True,
                 "ON - every drive logs rig\ffb_trace.csv + FFBlog.txt "
                 "(turn off when done)" if diag else "off"))
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
    ENV_LABELS = ["emulator (vunit.exe)", "DSP boot ROMs",
                  "force feedback plugin", "force feedback wheel",
                  "FFB diagnostics"]
    for label in ENV_LABELS:
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
        status = {label: (ok, detail) for label, ok, detail in env_status()}
        for (dot, det), label in zip(envrows, ENV_LABELS):
            if label not in status:      # plugin absent: no wheel row
                dot.configure(text="-", fg="#666078")
                det.configure(text="(needs the force feedback plugin)")
                continue
            ok, detail = status[label]
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
            if v.get("set") and (v["parent"] or v["set"] == "crusnwld24"):
                # (device sets tms320c31/tms320c32 are parents too)
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

    def import_previous():
        src = filedialog.askdirectory(
            title="Pick your previous Cruis'n Collection folder")
        if not src:
            return
        if os.path.normcase(os.path.abspath(src)) ==                 os.path.normcase(os.path.abspath(run_rig.POC)):
            say("that's this folder - pick the OLD installation")
            return
        try:
            run_rig.import_previous_install(src, progress=say)
        except Exception as e:
            say(f"import failed: {e}")
        refresh()

    tk.Button(btns, text="Add ROM file(s)...", command=add_roms,
              **style).pack(side="left", padx=6)
    tk.Button(btns, text="Import previous version...",
              command=import_previous, **style).pack(side="left", padx=6)
    tk.Button(btns, text="Open ROMs folder",
              command=lambda: os.startfile(run_rig.ROMPATH)
              if os.path.isdir(run_rig.ROMPATH)
              else os.makedirs(run_rig.ROMPATH) or os.startfile(run_rig.ROMPATH),
              **style).pack(side="left", padx=6)
    def detect_wheel():
        import threading

        def choose(devices):
            # ambiguous: let the player pick the wheel BASE by name
            top = tk.Toplevel(root)
            top.title("Which device is your wheel?")
            top.configure(bg=BG)
            tk.Label(top, text="Pick your wheel base (not the shifter or "
                     "pedals):", bg=BG, fg=FG,
                     font=("Bahnschrift", 11)).pack(padx=16, pady=(12, 6))
            lb = tk.Listbox(top, width=60, height=min(8, len(devices)),
                            bg="#1d1830", fg=FG, font=("Consolas", 10))
            for name, guid in devices:
                lb.insert("end", f"{name}   ({guid})")
            lb.pack(padx=16, pady=6)
            lb.selection_set(0)
            result = {}

            def ok():
                sel = lb.curselection()
                if sel:
                    result["dev"] = devices[sel[0]]
                top.destroy()
            tk.Button(top, text="Use this device", command=ok,
                      **style).pack(pady=(6, 14))
            top.grab_set()
            root.wait_window(top)
            return result.get("dev")

        def work():
            try:
                say("detecting force-feedback devices - a game window "
                    "opens for about 30 seconds, just wait (the plugin "
                    "lists devices only once the game is running)...")
                devices = run_rig.detect_ffb_devices(progress=say)
                if not devices:
                    say("the plugin reported no joysticks - is the wheel "
                        "base connected and POWERED ON? Turn it on and "
                        "try again (FFBlog.txt beside vunit.exe has the "
                        "details)")
                    return
                say("devices: " + "; ".join(n for n, _ in devices))
                dev = run_rig.pick_ffb_device(devices)
                if dev is None:
                    # ambiguous: ask on the Tk main thread, wait here
                    import time
                    box = {}
                    root.after(0, lambda: box.update(dev=choose(devices)))
                    while "dev" not in box:
                        time.sleep(0.1)
                    dev = box["dev"]
                if dev is None:
                    say("no device chosen - force feedback left unset")
                    return
                if run_rig.set_ffb_device_guid(dev[1]):
                    say(f"force feedback wheel set: {dev[0]} ({dev[1]})")
                else:
                    say("could not write FFBPlugin.ini")
            except Exception as e:
                say(f"wheel detection failed: {e}")
            root.after(0, refresh)

        threading.Thread(target=work, daemon=True).start()

    def toggle_diag():
        on = not run_rig.ffb_diag_enabled()
        try:
            run_rig.set_ffb_diag(on)
        except Exception as e:
            say(f"could not switch FFB diagnostics: {e}")
            return
        say("FFB diagnostics ON: play for a minute, then Save support "
            "bundle - it includes the force trace and the plugin log."
            if on else "FFB diagnostics off.")
        refresh()

    tk.Button(btns, text="Detect wheel (FFB)", command=detect_wheel,
              **style).pack(side="left", padx=6)
    tk.Button(btns, text="FFB diagnostics", command=toggle_diag,
              **style).pack(side="left", padx=6)
    tk.Button(btns, text="Save support bundle", command=support,
              **style).pack(side="left", padx=6)
    tk.Button(btns, text="Launch Collection", command=launch,
              **style).pack(side="left", padx=6)

    say("Add your own ROM zips - any filename works, they are identified "
        "by their contents. Include the tiny tms320c31.zip / tms320c32.zip "
        "DSP boot ROM sets from your MAME romset. Updating from an older "
        "version in another folder? 'Import previous version' brings your "
        "ROMs, bindings, settings and wheel over.")
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
