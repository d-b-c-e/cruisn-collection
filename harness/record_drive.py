"""Record an attended drive using the collection's saved game and wheel settings."""
import argparse
from datetime import datetime
from pathlib import Path
import time

import collection
import run_rig
import world_distance
import usa_distance
import exotica_visibility
from session_clock import SessionClock, position


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game", required=True, help="usa, world, offroad or exotica")
    ap.add_argument("--output", type=Path, help="new case directory")
    ap.add_argument("--with-ffb", action="store_true", help="retain saved force for attended driving")
    ap.add_argument("--every", type=int, default=60, help="native snapshot interval; dense GL capture happens on replay")
    ap.add_argument("--title", help="name shown in the case and external clock")
    ap.add_argument("--no-clock", action="store_true", help="disable the external emulation timer")
    ap.add_argument("--clock-position", type=position, default=(12, 12), help="X:Y in screen pixels")
    world_distance.add_arguments(ap)
    usa_distance.add_arguments(ap)
    exotica_visibility.add_arguments(ap)
    args = ap.parse_args(argv)
    card = collection.resolve_game_alias(args.game)
    if not card:
        ap.error("unknown game")
    if args.every < 1:
        ap.error("--every must be positive")
    state = collection.load_config()
    rom = state.get("world_rom", "crusnwld24") if card == "crusnwld" else card
    if card == "crusnwld":
        rom, note = run_rig.resolve_world_rom(rom)
        if note:
            print(note, flush=True)
    try:
        args.world_trial = world_distance.configure(args, rom, {})
        args.usa_trial = usa_distance.configure(args, rom, {})
        args.exotica_trial = exotica_visibility.configure(args, rom, {})
    except ValueError as error:
        ap.error(str(error))
    output = args.output or Path(run_rig.POC) / "results" / "diagnostics" / (
        f"drive-{rom}-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    if output.exists():
        ap.error("recording directory already exists; choose a new name")
    print(f"Recording {rom} to {output.resolve()}", flush=True)
    print("Using saved scale, aspect, seams, steering, bindings and force profile.", flush=True)
    print("Physical FFB: " + ("saved strength (attended)" if args.with_ffb else "OFF"), flush=True)
    if args.world_trial:
        print(f"EXPERIMENTAL global distance: {args.world_trial}; selective scenery disabled for this recording.", flush=True)
    if args.usa_trial:
        print(f"EXPERIMENTAL USA global distance: {args.usa_trial}; route changes need attended acceptance.", flush=True)
    if args.exotica_trial:
        print(f"EXPERIMENTAL Exotica CPU visibility: {args.exotica_trial}; far plane unchanged.",flush=True)
    print("Drive normally. F12 ends the game; wait for 'recording recorded' afterward.", flush=True)
    clock = SessionClock(output / "record", args.title or f"Recording: {rom}", args.clock_position)
    if not args.no_clock:
        clock.start()
    try:
        return record(args, state, card, rom, output)
    finally:
        clock.close()


def record(args, state, card, rom, output):
    proc, hwnd = run_rig.launch_game_async(
        rom=rom, scale=state["scale"], crt=state["crt"],
        crackfill=state["crackfill"], margin=state["margin"],
        steersens=state["steersens"].get(card),
        steercurve=state["steercurve"].get(card),
        ffb=int(state.get("ffb", 50)) if args.with_ffb else 0,
        record_case=str(output), record_every=args.every,
        record_with_ffb=args.with_ffb, record_clock=not args.no_clock,
        record_world_trial=args.world_trial, record_usa_trial=args.usa_trial,
        record_exotica_trial=args.exotica_trial)
    if args.title:
        proc.recording.manifest["title"] = args.title
    while proc.poll() is None and (not hwnd or run_rig.u32.IsWindow(hwnd)):
        time.sleep(0.5)
    result = run_rig.wait_or_kill(proc)
    print("Game closed; finishing snapshot encoding and recording validation...", flush=True)
    proc.recording.finish(result)
    return 0 if proc.recording.manifest["status"] == "recorded" else 1


if __name__ == "__main__":
    raise SystemExit(main())
