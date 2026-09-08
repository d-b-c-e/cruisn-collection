# Exotica admission evidence

`verify_archive.py` validates the 83-entry derived archive and recomputes the
admission, sphere, input and timing conclusions. It requires the adjacent
`2026-09-08-exotica-far-distance` companion archive, but no ROMs or third-party
Python packages. Strict frame and scene comparison failures remain failures.

## Additional depth-state receipt

`state-bias.json` and `analyze_state_bias.py` are a later, separate receipt; they
do not modify the original archive or its manifest. The report binds both raw
submission files by SHA256 and lists every matched quad whose bias changes.
All 814 changed biases are 2047 → 0, with unique geometry in both captures and
the bias branch active in both. Two other geometry associations are ambiguous
and marked separately. Geometry association does not establish original object
identity, draw order, or a visible-pixel effect.

From the collection repository root, recompute against the retained local
captures with standard Python:

```powershell
python results/proof/2026-09-08-exotica-admission/analyze_state_bias.py `
  results/diagnostics/exotica-streaming-20260908/scene-coherent/run/zeus-capture/records.bin `
  results/diagnostics/exotica-streaming-20260908/scene-admit160/run/zeus-capture/records.bin `
  --check results/proof/2026-09-08-exotica-admission/state-bias.json
```

The raw submission captures are local diagnostic inputs and are not included
in this derived archive. Unlike its numerical branch checks, this additional
state receipt requires those inputs to independently recompute its association.
The [review](../../../docs/reviews/2026-09-08-exotica-admission.md) describes the
next register-provenance investigation and the retained limits.
