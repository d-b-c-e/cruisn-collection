"""Portable recording metadata and replay validation, without device access.

MAME INP records effective digital and analog port state, including analog
interpolation. This module retains the initial configuration and evidence needed
to check whether a specific recording actually replays deterministically.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import shutil
import subprocess

from diagnostic_runtime import ROOT, diagnostic_env, new_run
from verification import image_signature, required_files, sha256_file, write_json
from raw_snapshots import convert_raw_snapshots

STATE_DIRS = ("ini", "cfg", "nvram", "ctrlr")
WRITABLE_DIRS = {"-inipath": "ini", "-cfg_directory": "cfg",
                 "-nvram_directory": "nvram", "-ctrlrpath": "ctrlr",
                 "-snapshot_directory": "snap", "-state_directory": "state",
                 "-input_directory": "input", "-diff_directory": "diff"}


def set_option(command, option, value):
    result = list(command)
    if option in result:
        index = result.index(option)
        result[index + 1] = str(value)
    else:
        result.extend((option, str(value)))
    return result


def tree_hashes(directory):
    directory = Path(directory)
    return {p.relative_to(directory).as_posix(): sha256_file(p)
            for p in sorted(directory.rglob("*")) if p.is_file()}


def git_identity(directory):
    try:
        revision = subprocess.check_output(["git", "-C", str(directory), "rev-parse", "HEAD"],
                                            stderr=subprocess.DEVNULL, text=True).strip()
        dirty = subprocess.check_output(["git", "-C", str(directory), "status", "--porcelain"],
                                         stderr=subprocess.DEVNULL, text=True).strip()
        return {"commit": revision, "dirty": bool(dirty)}
    except (OSError, subprocess.CalledProcessError):
        return None


def rom_hashes(rompath, rom):
    """Hash candidate containers for this set and its MAME parent chain.

    Clone parent names are recorded by prepare() using -listxml. Fail closed if
    this installation stores ROMs outside zip/7z containers: add that layout
    explicitly before claiming an identity match.
    """
    found = {}
    for directory in str(rompath).split(";"):
        for extension in (".zip", ".7z"):
            p = Path(directory) / (rom + extension)
            if p.is_file():
                found[str(p.resolve())] = sha256_file(p)
    return found


def read_trace(path):
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        if fields[:4] != ["frame", "emulated_seconds", "host_seconds", "speed_percent"]:
            raise ValueError("invalid session trace header")
        rows = list(reader)
    if any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError("incomplete session trace row")
    if not rows or [int(r["frame"]) for r in rows] != list(range(1, len(rows) + 1)):
        raise ValueError("session trace is empty, truncated or has nonconsecutive frames")
    times = [float(r["emulated_seconds"]) for r in rows]
    if any(not math.isfinite(t) for t in times) or any(a >= b for a, b in zip(times, times[1:])):
        raise ValueError("emulated time must be finite and strictly increasing")
    return fields, rows


def session_evidence(directory, every, returncode, *, require_gl=False):
    directory = Path(directory)
    if returncode != 0:
        raise ValueError(f"emulator exit code {returncode}")
    fields, rows = read_trace(directory / "frames.csv")
    stdout = (directory / "launch.log").read_text(encoding="utf-8", errors="replace")
    stderr_path = directory / "stderr.log"
    stderr = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.exists() else ""
    if "render stream failed" in stdout + stderr:
        raise ValueError("renderer fell back after losing its stream")
    receipts = [int(n) for n in re.findall(r"session.lua: snapshot at frame (\d+)", stdout)]
    stops = [int(n) for n in re.findall(r"session.lua: stopped at frame (\d+)", stdout)]
    frames = list(range(every, len(rows) + 1, every))
    if not frames:
        raise ValueError("recording is shorter than one snapshot interval")
    if receipts != frames or stops != [len(rows)]:
        raise ValueError("snapshot receipts or clean-stop receipt missing/inconsistent")
    expected = [f"frame_{n:08d}.png" for n in frames]
    if sorted(p.name for p in (directory / "snap").glob("*.png")) != expected:
        raise ValueError("session snapshot manifest differs")
    shots = {str(n): image_signature(directory / "snap" / name)
             for n, name in zip(frames, expected)}
    coverage = {f: {"min": min(int(r[f]) for r in rows),
                     "max": max(int(r[f]) for r in rows),
                     "distinct": len({r[f] for r in rows})} for f in fields[4:]}
    evidence = {"frames": len(rows), "columns": fields, "snapshots": shots,
            "input_coverage": coverage,
            "trace_sha256": sha256_file(directory / "frames.csv")}
    raw = directory / "raw-snap"
    if raw.exists():
        expected_raw = [f"frame_{n:08d}.raw" for n in frames]
        if sorted(p.name for p in raw.iterdir()) != expected_raw:
            raise ValueError("raw snapshot manifest differs")
        evidence["raw_sha256"] = {name: sha256_file(raw / name) for name in expected_raw}
    index = directory / "gl-snap" / "captures.csv"
    if require_gl or index.exists():
        with open(index, newline="", encoding="utf-8") as stream:
            captures = list(csv.DictReader(stream))
        if not captures or len({r["file"] for r in captures}) != len(captures):
            raise ValueError("GL capture index is empty or has duplicate files")
        if any(Path(r["file"]).name != r["file"] for r in captures):
            raise ValueError("GL capture filename must be local to its run")
        required_files(directory / "gl-snap", [r["file"] for r in captures])
        evidence["gl_captures"] = {
            "scope": "async presentation, labeled by last received stream frame; not a native frame fence",
            "count": len(captures), "dropped_messages": max(int(r["dropped_messages"]) for r in captures),
            "index_sha256": sha256_file(index),
            "files": {r["file"]: image_signature(directory / "gl-snap" / r["file"]) for r in captures}}
        if evidence["gl_captures"]["dropped_messages"]:
            raise ValueError("GL stream lost persistent rendering state")
        if "completed_frame" in captures[0]:
            from gl_frames import read_completed_frames
            completed = read_completed_frames(directory / "gl-snap")
            evidence["gl_captures"].update(scope="completed GL frame pixels",
                completed_frames=list(completed))
    return evidence


def compare_evidence(reference_dir, replay_dir, reference, replay):
    if reference["frames"] != replay["frames"] or reference["columns"] != replay["columns"]:
        raise ValueError("record/replay frame count or input columns differ")
    fields, a = read_trace(Path(reference_dir) / "frames.csv")
    _, b = read_trace(Path(replay_dir) / "frames.csv")
    deterministic = [f for f in fields if f not in ("host_seconds", "speed_percent")]
    bad_inputs = [int(x["frame"]) for x, y in zip(a, b)
                  if any(x[f] != y[f] for f in deterministic)]
    if reference["snapshots"].keys() != replay["snapshots"].keys():
        raise ValueError("record/replay snapshot frame IDs differ")
    bad_pixels = [int(n) for n, value in reference["snapshots"].items()
                  if value != replay["snapshots"][n]]
    return {"passed": not bad_inputs and not bad_pixels,
            "input_or_time_mismatches": len(bad_inputs), "first_input_mismatches": bad_inputs[:20],
            "pixel_mismatches": len(bad_pixels), "first_pixel_mismatches": bad_pixels[:20]}


class Recording:
    def __init__(self, output, every=60, stop_frame=0, snapshot_mode="raw", with_ffb=False):
        if every < 1 or stop_frame < 0:
            raise ValueError("snapshot interval must be positive and stop frame nonnegative")
        self.path = new_run("recording", output)
        self.every, self.stop_frame = every, stop_frame
        if snapshot_mode not in ("png", "raw"):
            raise ValueError("snapshot mode must be png or raw")
        self.snapshot_mode = snapshot_mode
        self.with_ffb = with_ffb
        self.manifest = None

    def prepare(self, command, env, rig, *, stimulus=None):
        """Freeze the already-prepared launch configuration, then run a copy."""
        rig = Path(rig)
        if self.with_ffb and stimulus:
            raise ValueError("physical FFB is only allowed during an attended live recording")
        initial = self.path / "initial"
        initial.mkdir()
        for name in STATE_DIRS:
            source = rig / name
            if source.is_dir():
                shutil.copytree(source, initial / name)
            else:
                (initial / name).mkdir()
        if (rig / "collection.ini").exists():
            shutil.copy2(rig / "collection.ini", initial / "collection.ini")
        shutil.copy2(ROOT / "lua" / "session.lua", initial / "session.lua")
        if stimulus:
            shutil.copy2(stimulus, initial / "stimulus.inp")
        settings = {k: v for k, v in diagnostic_env(env).items()
                    if k.startswith(("MIDV_", "MIDZ_"))}
        if self.with_ffb:
            settings["MIDV_FFB"] = env.get("MIDV_FFB", "0")
        # External paths whose contents affect emulation are retained and re-bound.
        if settings.get("MIDV_PATCH"):
            shutil.copy2(settings["MIDV_PATCH"], initial / "game-patch.txt")
            settings["MIDV_PATCH"] = "@initial/game-patch.txt"
        exe = Path(command[0]).resolve()
        binary = self.path / "binary"
        binary.mkdir()
        shutil.copy2(exe, binary / "vunit.exe")
        command = ["@binary/vunit.exe", *command[1:]]
        dependencies = {"vunit.exe": sha256_file(binary / "vunit.exe")}
        for name in ("SDL2.dll", "force-profiles.ini", "force-profiles.user.ini"):
            source = exe.parent / name
            if source.exists():
                dependencies[name] = sha256_file(source)
                shutil.copy2(source, binary / name)
                shutil.copy2(source, initial / name)
        rom = command[1]
        rompath = command[command.index("-rompath") + 1]
        from xml.etree import ElementTree as ET
        xml = subprocess.check_output([str(exe), rom, "-listxml"], timeout=30,
                                      env=diagnostic_env(), stderr=subprocess.PIPE)
        machine = ET.fromstring(xml).find(f"machine[@name='{rom}']")
        if machine is None:
            raise ValueError(f"no MAME identity for {rom}")
        sets = {rom, machine.get("romof"), machine.get("cloneof")} - {None}
        # Device ROMs (e.g. the TMS320 boot ROM) also affect reproducibility.
        sets.update(d.get("name") for d in machine.findall("device_ref") if d.get("name"))
        roms = {}
        for name in sorted(sets):
            roms.update(rom_hashes(rompath, name))
        if not roms:
            raise ValueError("no ROM zip/7z containers found to fingerprint")
        self.manifest = {"schema": 1, "status": "recording", "rom": rom,
            "snapshot_mode": self.snapshot_mode,
            "origin": "synthetic-inp" if stimulus else "live-input",
            "attended_ffb": self.with_ffb,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "every": self.every, "stop_frame": self.stop_frame,
            "command": list(command), "settings": settings,
            "executable_source": str(exe),
            "dependencies": dependencies, "rom_containers": roms,
            "initial_hashes": tree_hashes(initial),
            "collection_source": git_identity(ROOT), "emulator_source": git_identity(exe.parent)}
        write_json(self.path / "case.json", self.manifest)
        runtime = self.path / "record"
        cmd, launch_env = prepare_run(self.path, self.manifest, runtime, playback=False)
        return cmd, launch_env, runtime

    def finish(self, returncode):
        if self.manifest is None:
            return
        try:
            required_files(self.path / "record" / "input", ["session.inp"])
            convert_raw_snapshots(self.path / "record")
            self.manifest["evidence"] = session_evidence(self.path / "record", self.every, returncode,
                require_gl=bool(self.manifest["settings"].get("MIDV_GL_SNAP") or self.manifest["settings"].get("MIDZ_GL_SNAP")))
            self.manifest["inp_sha256"] = sha256_file(self.path / "record" / "input" / "session.inp")
            self.manifest["status"] = "recorded"
        except (ValueError, OSError) as exc:
            self.manifest["status"] = "failed"
            self.manifest["error"] = str(exc)
        self.manifest["returncode"] = returncode
        write_json(self.path / "case.json", self.manifest)
        print(f"recording {self.manifest['status']}: {self.path}")


def prepare_run(case, manifest, runtime, *, playback, headless=False):
    case, runtime = Path(case), Path(runtime)
    shutil.copytree(case / "initial", runtime)
    command = list(manifest["command"])
    if command[0] == "@binary/vunit.exe":
        command[0] = str(case / "binary" / "vunit.exe")
    for option, name in WRITABLE_DIRS.items():
        (runtime / name).mkdir(exist_ok=True)
        command = set_option(command, option, runtime / name)
    command = set_option(command, "-autoboot_script", runtime / "session.lua")
    command = set_option(command, "-autoboot_delay", 0)
    command = set_option(command, "-snapview", "native")
    command = set_option(command, "-output", "none")
    command = set_option(command, "-frameskip", 0)
    command += ["-noplugins", "-noautosave", "-norewind", "-noautoframeskip"]
    settings = dict(manifest["settings"])
    if settings.get("MIDV_PATCH", "").startswith("@initial/"):
        settings["MIDV_PATCH"] = str(runtime / "game-patch.txt")
    settings.update(SNAP_EVERY=str(manifest["every"]),
                    SNAP_STOP=str(manifest["evidence"]["frames"] if playback else manifest["stop_frame"]),
                    SNAP_SESSION_LOG=str(runtime / "frames.csv"),
                    MIDV_GL_STATEFILE=str(runtime / "gl_state.txt"),
                    MIDV_FFB_SOURCE_TRACE=str(runtime / "force-source.csv"),
                    MIDV_SIGNAL_TRACE=str(runtime / "signals.csv"),
                    MIDV_FFB_TRACE=str(runtime / "ffb_trace.csv"))
    # Remove path-based one-off diagnostics that could overwrite unrelated evidence.
    for k in list(settings):
        if k in ("MIDV_GL_SNAP", "MIDZ_GL_SNAP"):
            destination = runtime / "gl-snap"
            destination.mkdir(exist_ok=True)
            settings[k] = str(destination)
        elif k.endswith(("_SNAP", "_STATEDUMP_DIR", "_QUADLOG", "_CAPTURE", "_RAMDUMP_DIR")):
            del settings[k]
    env = diagnostic_env(settings)
    if not playback and not headless and manifest.get("attended_ffb") and manifest.get("origin") == "live-input":
        env["MIDV_FFB"] = settings.get("MIDV_FFB", "0")
    if manifest.get("snapshot_mode") == "raw":
        (runtime / "raw-snap").mkdir()
        env["SNAP_RAW_DIR"] = str(runtime / "raw-snap")
    # Only an explicitly attended live recording retains the selected wheel force.
    # Replay and synthetic recording remain output-free regardless of the manifest.
    if playback:
        shutil.copy2(case / "record" / "input" / "session.inp", runtime / "input" / "session.inp")
        command = set_option(command, "-playback", "session.inp")
        command += ["-exit_after_playback"]
    else:
        command = set_option(command, "-record", "session.inp")
        if manifest.get("origin") == "synthetic-inp":
            shutil.copy2(runtime / "stimulus.inp", runtime / "input" / "stimulus.inp")
            command = set_option(command, "-playback", "stimulus.inp")
    if headless:
        for option, value in (("-video", "none"), ("-sound", "none")):
            command = set_option(command, option, value)
        command += ["-nothrottle", "-nojoystick", "-nomouse", "-nolightgun"]
        for k in ("MIDV_GL", "MIDV_LIVE", "MIDZ_GL"):
            env.pop(k, None)
    return command, env
