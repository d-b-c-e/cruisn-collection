# Global pending admission and source-assisted research evidence

All emulator runs used native `e8b8fc3be9c`, physical FFB off. No new native
distance code was built. `runs.json` preserves outcomes, source report hashes,
probe provenance, settings and capture receipts. Full run directories remain
under ignored `results/diagnostics/`.

`global-motion-control.lua` and `global-motion-lead8.lua` combine the read-only
camera/ADC trace with bounded pending admission. They differ in the baked pending
lead default. Both use native scenery off, native scenery activation lead zero.
Their reports cover the original attended extended-Germany case through6304;
completed GL frames5900..6300 every2, small-window output, fourfold internal scale.

The control passes original-prefix identity. The candidate has seven different
native snapshots and the route comparison FAILs: ADC values/frame/PC sequences
agree, ADC timestamps do not, camera first differs6184. The contact sheet shows
later driving-state changes. This is not an accepted visual-only fix.

The two named subdirectories contain the original camera and ADC CSVs.
`compare_world_motion.compare()` on those archived traces reproduces
`global-motion-comparison.json` exactly, including its failed status and hashes.
Git attributes preserve the evidence bytes across Windows/Linux checkouts;
automatic newline conversion would otherwise change those source hashes.

Example reproduction into a NEW output directory:

```powershell
python harness/replay.py results/diagnostics/world-germany-extended-20260906 --candidate E:/Source/mame-src/vunit.exe --scenery off --scenery-lead 0 --probe-script results/proof/2026-09-06-global-distance/global-motion-control.lua --until-frame 6304 --small-window --gl-capture 5900:6300 --gl-every 2 --gl-max 202 --output results/diagnostics/global-motion-control-repeat
```

For the candidate, substitute `global-motion-lead8.lua` and a distinct output
directory. Candidate FAIL against the original pictures is expected; inspect
diagnostic errors and camera state independently. Use the committed executable
hash from the assessment, or label the result a new-binary comparison. The local
recording/ROMs are not distributed in this proof.

`mountain-sort-key-existing.lua` observes the already allocated CB2314 at 11C04
over 5990..6230; run with scenery all, lead 0/8 to compare depth-key updates.
Control 189 writes, candidate 575 writes; both complete, neither passes the original
attended recording's image identity. `mountain-sort-key-wrong-target.lua` selects
CB2315 and correctly fails the initial model guard. Its error is required negative
evidence. The default allocation probe continues to require an observed assignment.

`pending-global-control.lua`/`pending-global-lead8.lua` are the earlier combined
projection-attribution probes with scenery all, lead 0. `selective-tree-activation.lua`
is the four-model comparison retained for completeness. Neither is a new product
option or the recommended global architecture.
