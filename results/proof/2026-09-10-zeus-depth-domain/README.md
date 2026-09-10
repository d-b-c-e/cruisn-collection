# Wider Zeus depth diagnostics

Run `python results/proof/2026-09-10-zeus-depth-domain/verify.py` to check archived
source identity, clocks, timing and ordered fingerprints. GPU checks and the local
suite remain hash-bound receipts; the verifier does not execute them.

To rerun the ROM-free GPU checks on an idle rig:

```powershell
python harness/verify_zeus_depth_domain.py --report results/depth-domain-new.json
python harness/verify_zeus_depth_mirror.py --report results/depth-mirror-new.json
```

Output paths must be new. The first checks every original 24-bit input depth;
the second exercises the actual Zeus shader's materials/depth behavior. Neither
is a live game mirror or an extended-distance implementation. Initial failed
experiments remain explicitly failed. No raw game resources are archived.

See the [review](../../../docs/reviews/2026-09-10-zeus-depth-domain.md) for the
quantization finding, measured performance cost and next live-renderer work.
