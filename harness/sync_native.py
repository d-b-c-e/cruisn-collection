"""Check/copy project-owned native helpers into the separately committed MAME tree."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mame", type=Path)
    ap.add_argument('--ux', action='store_true', help='only isolated consumer UX helpers; requires explicit --mame')
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    if args.ux and args.mame is None:
        ap.error('--ux requires an explicit isolated --mame worktree')
    args.mame = args.mame or Path(r'E:\Source\mame-src')
    failed = False
    endpoint_helpers = ("phase_timing.h", "checked_journal_close.h", "exotica_reset.h", "exotica_runtime.h", "exotica_bootstrap.h", "diagnostic_count.h", "exotica_journal_policy.h", "diagnostic_journal.h", "world_active_roads.h", "exotica_command_owners.h", "exotica_model_endpoint.h", "exotica_admissions.h", "zeus_endpoint_pair.h", "exotica_scene_endpoint.h", "vunit_far_coverage.h", "vunit_distance_fade.h", "exotica_pool_clear.h")
    private_materials = endpoint_helpers + ("page_image.h", "written_pages.h", "zeus_host_materials.h", "zeus_retained_materials.h", "command_ring_fence.h", "exotica_active.h", "exotica_active_capture.h", "zeus_margin_packet.h", "zeus_wide_packet.h", "zeus_resource_lease.h", "scenery_lifetimes.h", "exotica_waiting.h", "exotica_waiting_handover.h", "exotica_composition.h", "exotica_fade.h")
    names = ('ffb_device_selection.h',) if args.ux else private_materials + ("capture_writer.h", "capture_bitmap.h", "pause_cheats.h", "pause_cheats_win.h", "hud_speed_filter.h", "hud_numeric_speed.h", "hud_drivetrain.h", "motor_signal.h", "tjunctions.h", "checked_patch.h", "retained_texture.h", "world_scenery.h", "world_distance.h", "usa_distance.h", "offroad_distance.h", "exotica_visibility.h", "cpu_upload_spans.h", "scenery_c31.h", "vunit_runtime.h", "vunit_journal_policy.h", "vunit_bootstrap_profile.h", "world_host_layout.h", "world_host_scenery.h", "world_future_sections.h", "world_road_scenery.h", "usa_model.h", "usa_host_scenery.h", "usa_future_sections.h", "offroad_model.h", "offroad_transform.h", "offroad_future_sections.h", "offroad_partial_sections.h", "offroad_host_scenery.h", "exotica_future_sections.h", "exotica_source_cache.h", "exotica_transform.h", "exotica_state.h", "exotica_scene.h", "exotica_scene_capture.h", "zeus_model.h", "zeus_model_bounds.h", "zeus_state.h", "zeus_render_policy.h")
    for name in names:
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
