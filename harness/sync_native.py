"""Check/copy project-owned native helpers into the separately committed MAME tree."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mame", type=Path, default=Path(r"E:\Source\mame-src"))
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    failed = False
    private_materials = ("page_image.h", "written_pages.h", "zeus_host_materials.h", "command_ring_fence.h", "exotica_active.h")
    for name in private_materials + ("capture_writer.h", "capture_bitmap.h", "pause_cheats.h", "pause_cheats_win.h", "hud_speed_filter.h", "hud_numeric_speed.h", "hud_drivetrain.h", "motor_signal.h", "tjunctions.h", "checked_patch.h", "retained_texture.h", "world_scenery.h", "world_distance.h", "usa_distance.h", "offroad_distance.h", "exotica_visibility.h", "cpu_upload_spans.h", "scenery_c31.h", "world_host_layout.h", "world_host_scenery.h", "world_future_sections.h", "world_road_scenery.h", "usa_model.h", "usa_host_scenery.h", "usa_future_sections.h", "offroad_model.h", "offroad_transform.h", "offroad_future_sections.h", "offroad_host_scenery.h", "exotica_future_sections.h", "exotica_source_cache.h", "exotica_transform.h", "exotica_state.h", "exotica_scene.h", "exotica_scene_capture.h", "zeus_model.h", "zeus_model_bounds.h", "zeus_state.h", "zeus_render_policy.h"):
        source = ROOT / "native" / name
        target = args.mame / "src" / "mame" / "midway" / "cruisn" / name
        expected = source.read_bytes().replace(b"\r\n", b"\n")
        actual = target.read_bytes().replace(b"\r\n", b"\n") if target.exists() else None
        if actual == expected:
            continue
        if args.write:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(expected)
            print(f"updated {target}")
        else:
            print(f"native helper differs or is missing: {target}")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
