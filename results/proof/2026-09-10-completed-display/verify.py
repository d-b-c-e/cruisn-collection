from pathlib import Path
import hashlib,json
from display_target import verify_completed_size
root=Path(__file__).parent
read=lambda n:json.loads((root/n).read_text(encoding="utf-8"))
for n,h in read("manifest.json")["files"].items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h,n
identity=read("source-identity.json");checks=read("report.json");change=read("source-changes.json")
assert hashlib.sha256("".join(f"{k}\0{v}\n" for k,v in sorted(identity["files"].items())).encode()).hexdigest()==identity["sha256"]==checks["source_identity"]==checks["source_identity_after"]==change["current_identity"]
assert change["files"]==["harness/display_target.py","harness/replay.py","tests/test_display_target.py"]
assert read("unit-tests.json")==dict(passed=True,tests=337,skipped=0,errors=0,failures=0)
assert checks["passed"] and checks["groups"]==["python"]
for name,case in read("cases.json").items():
    try:
        result=verify_completed_size((3840,2160),case["frames"])
        assert name!="depth-mirror-disabled" and result["passed"]
    except ValueError:
        assert name=="depth-mirror-disabled"
print("PASS wrong-size rejection, two4K controls,337 Python receipt and three-file source change. No new native/GPU/game run.")
