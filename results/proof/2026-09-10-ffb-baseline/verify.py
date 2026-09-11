from pathlib import Path
import hashlib,json
here=Path(__file__).parent;root=here.resolve().parents[2]
read=lambda p:json.loads(p.read_text(encoding="utf-8"))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in read(here/"manifest.json").items():assert sha(here/name)==digest,name
r=read(here/"summary.json")
for name,digest in r["bound_source_files"].items():assert sha(root/name)==digest,name
assert r["passed"] and r["common_native_source"] and not r["normalization_accepted"]
assert not r["physical_force"] and not r["matched_segments"]
assert set(r["cases"])=={"usa","world","offroad","exotica"}
for game,item in r["cases"].items():
    assert item["replay_passed"] and item["physical_ffb"]=="0"
    assert item["native_sha256"]=="97cd738c6b89f59a7523c9494285c5ee625e9f5041622f542983d94173b37d7a"
    assert [s["requested"] for s in item["strengths"]]==[0,25,50,80,100]
    for s in item["strengths"]:
        e=(s["requested"]*80+50)//100 if game=="exotica" else s["requested"]
        assert s["effective"]==s["metrics"]["strength"]==e
        assert 0<=s["metrics"]["peak_abs"]<=e/100+1e-6
        assert s["metrics"]["motor_samples"]==item["samples"]
        if e==0:assert s["metrics"]["rms"]==s["metrics"]["peak_abs"]==0
assert r["alias_regression"]["actual_usa_host_trace"]["motor_samples"]==1374
print("PASS source/artifact hashes and20 algorithm/common-candidate receipts; matched normalization and physical acceptance remain false")
