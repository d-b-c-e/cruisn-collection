from pathlib import Path
import hashlib,json,sys
here=Path(__file__).parent;root=here.resolve().parents[2]
sys.path.insert(0,str(root/"harness"))
from release_identity import source_identity
read=lambda name:json.loads((here/name).read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read("manifest.json")
assert set(manifest)=={p.name for p in here.iterdir() if p.is_file() and p.name!="manifest.json"}
for name,digest in manifest.items():assert sha(here/name)==digest,name
identity=source_identity(root);assert identity==read("source-identity.json")
r=read("local-checks.json");u=read("unit-tests.json")
assert r["passed"] and r["source_identity"]==r["source_identity_after"]==identity["sha256"]
assert r["groups"]==["python","native","gpu"] and len(r["steps"])==142 and all(s["returncode"]==0 for s in r["steps"])
assert sum(s["name"].startswith("run-") for s in r["steps"])==50
assert u["passed"] and u["tests"]==358 and u["skipped"]==u["errors"]==u["failures"]==0
r=read("actual-scenes.json");assert r["passed"] and r["native_event_receipt"]["passed"]
assert r["helper_sha256"]==sha(root/"native/exotica_waiting.h")
assert r["native_events_sha256"]=="5a1f9004fa1d5cb7aa6e3832d911e1eca90f105bfc802a851d10c08eb182cd8b"
assert len(r["cases"])==30
expected={3900:252,5072:155,5644:298,6330:52,7187:1}
assert {(c["frame"],c["multiplier"],c["complete_fade"]) for c in r["cases"]}=={(f,m,a) for f in expected for m in (1,2,3) for a in (0,1)}
for frame,count in expected.items():
    cases=[c for c in r["cases"] if c["frame"]==frame]
    assert all(c["owners"]==count and 0<c["events"]<=86376 for c in cases)
    assert len({c["owners_sha256"] for c in cases})==len({c["event_prefix_sha256"] for c in cases})==1
print("PASS source/file hashes,30 actual-scene receipts and full local-check consistency; raw execution remains receipts")
