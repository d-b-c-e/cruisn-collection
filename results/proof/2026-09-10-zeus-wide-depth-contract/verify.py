from pathlib import Path
import hashlib,json
root=Path(__file__).parent
read=lambda n:json.loads((root/n).read_text(encoding="utf-8"))
for n,h in read("manifest.json")["files"].items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h,n
identity=read("source-identity.json");checks=read("report.json");change=read("source-changes.json")
assert hashlib.sha256("".join(f"{k}\0{v}\n" for k,v in sorted(identity["files"].items())).encode()).hexdigest()==identity["sha256"]==checks["source_identity"]==checks["source_identity_after"]==change["current_identity"]
assert len(identity["files"])==497 and len(change["files"])==7
assert checks["passed"] and len(checks["steps"])==132 and all(s["returncode"]==0 for s in checks["steps"])
assert sum(s["name"].startswith("run-") for s in checks["steps"])==47
assert read("unit-tests.json")==dict(passed=True,tests=340,skipped=0,errors=0,failures=0)
gpu=read("zeus-wide-depth.json");reference=read("local-gpu-reference.json")
assert gpu["passed"] and len(gpu["cases"])==292 and sum(c["steps"] for c in gpu["cases"])==636
assert gpu["cases"]==reference["cases"] and gpu["source_sha256"]==reference["source_sha256"]
assert all(c["passed"] and len(c["hashes"])==c["steps"] for c in gpu["cases"])
assert {(c["scale"],c["page"]) for c in gpu["cases"]}=={(1,0),(1,400),(4,0),(4,400)}
assert not read("alpha-reference-failure.json")["passed"]
assert read("zeus-depth-domain.json")["passed"] and read("zeus-depth-mirror.json")["passed"]
python=read("independent-packet.json");native=read("native-packet.json")
assert python["passed"] and native["passed"] and sum(r["quads"] for r in python["captured"])==14696
assert {r["file"]:r["sha256"] for r in python["captured"]}==native["files"] and "captured quads=14696" in native["stdout"]
print("PASS source identity and hash-bound340Python/47native/132command,292GPUcase/636step,14696captured-quad receipts. Standalone contracts only; no new MAME build/live wider scene/default acceptance.")
