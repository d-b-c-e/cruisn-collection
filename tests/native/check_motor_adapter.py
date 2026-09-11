"""Exercise the compiled production algorithms with raw/clamped motor inputs."""
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]


def main():
    exe = str(Path(sys.argv[1]).resolve())
    with tempfile.TemporaryDirectory() as directory:
        directory = Path(directory)
        fixture = ROOT / "fixtures/signals/clamped-hit.csv"
        for source_format in (True, False):
            if not source_format:
                fixture = directory / "motor.csv"
                fixture.write_text("ms,raw,byte\n0,0,0\n100,126,20\n200,0,0\n400,0,0\n")
            for enhanced in (False, True):
                stages = directory / "stages.csv"
                result = subprocess.run([exe, str(fixture), str(ROOT / "lib/toolkit/profiles"),
                    "cruisn-vunit@2", "50", str(stages)] + (["--impacts"] if enhanced else []),
                    check=True, capture_output=True, text=True)
                metrics = json.loads(result.stdout)
                assert metrics["events_ms"] == ([100] if enhanced else []), metrics
                assert 0 < metrics["peak_abs"] <= 0.5, metrics
                assert metrics["full_strength_fraction"] == 0, metrics
                rows = list(csv.DictReader(io.StringIO(stages.read_text())))
                hit = next(row for row in rows if row["ms"] == "100")
                assert hit["motor_byte"] == "20" and hit["raw_byte"] == "126", hit
                assert abs(float(hit["detector_input"])) > (0.99 if enhanced else 0.15), hit
                if not enhanced:
                    assert abs(float(hit["detector_input"])) < 0.16, hit
        # Current recordings name this output wheel_motor. Both names must
        # reproduce the same stages, including signed bytes and neutral 0x80.
        reference = None
        for output_name in ("wheel", "wheel_motor"):
            fixture = directory / (output_name + ".csv")
            fixture.write_text("ms,output,value\n# game crusnusa\n"
                + "\n".join(f"{ms},{output_name},{value}" for ms, value in
                    ((0, 0), (100, 126), (200, 130), (300, 128), (500, 0))) + "\n")
            stages = directory / (output_name + "-stages.csv")
            result = subprocess.run([exe, str(fixture), str(ROOT / "lib/toolkit/profiles"),
                "cruisn-vunit@2", "50", str(stages)], check=True, capture_output=True, text=True)
            current = (json.loads(result.stdout), stages.read_bytes())
            if reference is None:
                reference = current
                rows = list(csv.DictReader(io.StringIO(stages.read_text())))
                neutral = next(row for row in rows if row["ms"] == "300")
                assert neutral["motor_byte"] == "-128" and float(neutral["normalised"]) == 0
            else:
                assert current == reference, "motor aliases differ"
    print("PASS: raw collision detection survives adapter clamping; both trace formats agree")


if __name__ == "__main__":
    main()
