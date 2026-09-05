"""Create a labeled Cruis'n USA INP stimulus and record/replay it through MAME.

This is a scenario generator, not a human-input recorder. It uses the documented
MAME INP v3 port layout from this driver's source, refusing a different layout or
non-neutral seed. The recorded case still goes through MAME's actual INP writer.
"""
import argparse
import json
from pathlib import Path
import shutil
import struct
import sys
import zlib

from diagnostic_runtime import diagnostic_env, execute, new_run
from session_case import Recording, set_option
from verification import sha256_file, write_json
import replay

PORTS = (":ACCEL", ":BRAKE", ":CONF", ":DSW", ":FAKE", ":IN0", ":IN1", ":MOTION", ":WHEEL")
ANALOG = (":ACCEL", ":BRAKE", ":WHEEL")
STRIDE = 16 + len(PORTS) * 8 + len(ANALOG) * 13
SECOND = 10**18


def generate(seed_bytes, scenario):
    if (seed_bytes[:8] != b"MAMEINP\0" or seed_bytes[16:18] != b"\x03\x00" or
            seed_bytes[20:32].split(b"\0")[0] != b"crusnusa"):
        raise ValueError("requires a Cruis'n USA MAME INP v3.0 seed")
    payload = zlib.decompress(seed_bytes[64:])
    if len(payload) < STRIDE * 2 or len(payload) % STRIDE:
        raise ValueError("INP does not have the expected USA port layout")
    times = [s * SECOND + a for s, a, _ in
             (struct.unpack_from("<iqI", payload, n) for n in range(0, len(payload), STRIDE))]
    step = times[1] - times[0]
    if times[0] != 0 or step <= 0 or any(t != n * step for n, t in enumerate(times)):
        raise ValueError("seed has nonuniform or unexpected emulated input timing")
    template = payload[16:STRIDE]
    if any(payload[n + 16:n + STRIDE] != template for n in range(0, len(payload), STRIDE)):
        raise ValueError("seed must be neutral and have constant effective port state")
    frames = int(scenario["frames"])
    if not 1 <= frames <= 36000:
        raise ValueError("scenario must contain 1..36000 frames")
    offsets, analog_offsets = {}, {}
    at = 16
    for tag in PORTS:
        offsets[tag] = at
        at += 8
        if tag in ANALOG:
            analog_offsets[tag] = at
            at += 13
    for tag, offset in offsets.items():
        if struct.unpack_from("<I", payload, offset + 4)[0] != 0:
            raise ValueError(f"seed holds a digital input on {tag}")
    keys = scenario.get("analog", {})
    for tag, points in keys.items():
        if tag not in ANALOG or not points or points[0][0] != 0:
            raise ValueError("analog keyframes must name a USA axis and start at frame 0")
        previous = -1
        for frame, value in points:
            low = -1 if tag == ":WHEEL" else 0
            if not previous < frame <= frames or not low <= value <= 1:
                raise ValueError("invalid analog keyframe order or normalized value")
            previous = frame
    pulses = scenario.get("buttons", [])
    for p in pulses:
        if p["port"] not in PORTS or not 0 <= p["start"] < p["end"] <= frames:
            raise ValueError("invalid button pulse")
        if not 0 < p["mask"] <= 0xffffffff:
            raise ValueError("invalid button mask")
    previous_accum = {tag: struct.unpack_from("<i", payload, offset)[0]
                      for tag, offset in analog_offsets.items()}
    result = bytearray()
    cursors = {tag: 0 for tag in keys}
    for n in range(frames + 1):
        row = bytearray(struct.pack("<iqI", *divmod(n * step, SECOND), 1 << 20) + template)
        for p in pulses:
            if p["start"] <= n < p["end"]:
                offset = offsets[p["port"]] + 4
                value = struct.unpack_from("<I", row, offset)[0]
                struct.pack_into("<I", row, offset, value | p["mask"])
        for tag, points in keys.items():
            index = cursors[tag]
            while index + 1 < len(points) and points[index + 1][0] <= n:
                index += 1
            cursors[tag] = index
            value = points[index][1]  # step/hold; MAME retains analog interpolation
            raw = value * 65536 if tag == ":WHEEL" else (value * 2 - 1) * 65536
            offset = analog_offsets[tag]
            sensitivity = struct.unpack_from("<i", row, offset + 8)[0]
            if not 1 <= sensitivity <= 255:
                raise ValueError("unsupported analog sensitivity in seed")
            accum = int(raw * 100 / sensitivity)
            struct.pack_into("<ii", row, offset, accum, previous_accum[tag])
            previous_accum[tag] = accum
        result.extend(row)
    return seed_bytes[:64] + zlib.compress(result, 6)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("seed", type=Path, help="neutral completed run_replay_smoke.py case")
    ap.add_argument("scenario", type=Path)
    ap.add_argument("--output")
    ap.add_argument("--timeout", type=float, default=300)
    ap.add_argument("--candidate", type=Path, help="record with this emulator instead of the seed's archived binary")
    ap.add_argument("--gl", action="store_true", help="show the V-Unit GL renderer during the scripted drive")
    ap.add_argument("--patch", type=Path, help="explicit game-code patch for this new case")
    ap.add_argument("--gl-capture", help="short first:last stream-frame interval for live GL BMP captures")
    args = ap.parse_args(argv)
    work = new_run("scenario", args.output)
    seed = args.seed.resolve()
    manifest = json.loads((seed / "case.json").read_text(encoding="utf-8"))
    scenario = json.loads(args.scenario.read_text(encoding="utf-8"))
    if manifest["rom"] != "crusnusa" or manifest["evidence"]["columns"][4:] != list(PORTS):
        ap.error("requires a completed neutral USA case with the expected ports")
    stimulus = work / "stimulus.inp"
    stimulus.write_bytes(generate((seed / "record" / "input" / "session.inp").read_bytes(), scenario))
    shutil.copy2(args.scenario, work / "scenario.json")
    write_json(work / "provenance.json", {"kind": "synthetic-effective-input", "seed": str(seed),
               "scenario_sha256": sha256_file(args.scenario), "stimulus_sha256": sha256_file(stimulus)})
    command = list(manifest["command"])
    command[0] = str(args.candidate.resolve()) if args.candidate else str(seed / "binary" / "vunit.exe")
    command = set_option(command, "-seconds_to_run", scenario["frames"] // 50 + 30)
    settings = dict(manifest["settings"])
    if settings.get("MIDV_PATCH") == "@initial/game-patch.txt":
        settings["MIDV_PATCH"] = str(seed / "initial" / "game-patch.txt")
    if args.patch:
        settings["MIDV_PATCH"] = str(args.patch.resolve())
    if args.gl:
        command = set_option(command, "-video", "gdi")
        command = set_option(command, "-resolution", "1280x720")
        command += ["-window", "-throttle"]
        settings.update(MIDV_GL="1", MIDV_GL_SCALE="4", MIDV_GL_LOG="1")
    if args.gl_capture:
        first, last = [int(v) for v in args.gl_capture.split(":")]
        if not args.gl or not 0 <= first < last <= scenario["frames"] or last - first > 240:
            ap.error("GL capture requires --gl and an interval of 1..240 frames within the scenario")
        settings.update(MIDV_GL_SNAP="redirect-at-launch", MIDV_GL_SNAP_EVERY="1",
                        MIDV_GL_SNAP_FIRST=str(first), MIDV_GL_SNAP_LAST=str(last), MIDV_GL_SNAP_MAX="180")
    recording = Recording(str(work / "case"), every=scenario.get("snapshot_every", 60),
                           stop_frame=scenario["frames"])
    command, env, runtime = recording.prepare(command, diagnostic_env(settings),
                                               seed / "initial", stimulus=stimulus)
    result = execute(command, runtime, env, args.timeout)
    if (runtime / "stdout.log").exists():
        shutil.copy2(runtime / "stdout.log", runtime / "launch.log")
    recording.finish(result["returncode"])
    if recording.manifest["status"] != "recorded":
        return 1
    return replay.main([str(recording.path), "--headless", "--timeout", str(args.timeout),
                        "--output", str(work / "replay")])


if __name__ == "__main__":
    sys.exit(main())
