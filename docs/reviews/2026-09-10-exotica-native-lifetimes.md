# Native Exotica allocation and first-draw observation

The standalone lifetime tracker is now linked into a **separate diagnostic
candidate**, with explicit read-only observation. It reproduces the original
Lua allocation/source/first-submission event stream across a complete Amazon
drive and repeat. This establishes the ownership data needed to keep eligible
allocated scenery visible before the game first submits it. Waiting-object
selection and drawing are not yet linked into the live path.

## Candidate and contract

- Native commit `795fc77b68e40c88ec328be49a03bedd27300c04`.
- Frozen `build/candidates/795fc77b68e/vunit.exe`, SHA256
  `97cd738c6b89f59a7523c9494285c5ee625e9f5041622f542983d94173b37d7a`.
- 185 exported patches reconstruct tree
  `27098b964ce298fdde53c3696f44be1d38fdd78d` from base
  `ca48656c92325c821b85984952e96241d60c7aef`.
- Personal executable SHA256 remains
  `87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8`;
  public v0.5.0 and deployment are unchanged.

`--exotica-lifetimes observe` requires an explicit candidate, supported Exotica
revision, bounded first/last frames and physical FFB off. Absent/off mode is
inert. Native code validates the pool head/count/reset transactions and source
entry signatures, then records generation, reset epoch, source realm and first
original model submission. It does not alter guest memory, geometry, materials
or input timing. A partial initial capture permits explicitly counted unknown
pre-window frees; later reset removes that allowance.

The observer has finite frame, event and model-emission budgets. Malformed
configuration, stale generations, duplicate ownership and unsupported memory
domains fail explicitly. Python independently folds the CSV and validates final
counters. `last_submission` records observation at native-frame granularity;
it is not proof of an exact per-scene handover boundary.

## Full-drive evidence

Three runs use 8,860 recorded inputs: observe, repeat and disabled. Each preserves
7,060 original camera samples and 21,180 actual ADC reads with emulated times,
plus all 21 completed 3840×2160 CRT captures at frames 4650–4750, step 5.

Both observer runs match **86,375 original Lua event rows**, including actual
timestamps and every event field. Their additional initialization record has
matching initial head/count; the earlier Lua trace did not record an activation
timestamp to compare. The complete 86,376-row native CSV repeats byte-for-byte,
SHA256 `5a1f9004fa1d5cb7aa6e3832d911e1eca90f105bfc802a851d10c08eb182cd8b`.

| Counter | Both observer runs |
|---|---:|
| Pool transitions | 48,481 |
| Source bindings | 4,018 |
| Original standard-model emissions | 1,010,130 |
| Emissions joined to owned generations | 948,739 |
| Recorded first/fading/first-opaque submissions | 33,876 |
| First draws | 3,573 |
| Fading submissions | 30,308 |
| First opaque submissions | 1,126 |
| Epochs / initial unknown frees | 2 / 26 |

The disabled control produces no observer acknowledgement or CSV and preserves
the same route and display samples. Recorded speeds with diagnostic captures
are not an uncaptured performance comparison or full live-scene pixel coverage.

## Checks and retained failures

Full local checks pass: **358 Python tests, no skips; 49 native tests;
140 commands including GPU checks**. Source identity is
`4e41ca4409521afad76b3fa495c79f882d7ff58310b78df43cadb56ea12b9c8a`.

The fresh seven-default suite is **six PASS, one FAIL**. USA original/widescreen,
World 2.4 synthetic, World 2.5, Off Road and Exotica pass. World Germany reports
`renderer fell back after losing its stream`. Native stderr identifies a consumer
timeout at frame 875: 128,859,568 bytes queued in a 134,217,728-byte ring, zero
consumer bytes, 781 ms wait. The game exits normally, but the renderer result is
not acceptable. Cause and reproducibility remain under investigation; the
Exotica-only observer was disabled in this run. Do not relabel the suite PASS
or attribute this failure to the new observer without evidence.

An earlier suite attempt was interrupted after discovering another session's
MAME build overlapping its first case. The other session's build was left alone;
the incomplete attempt and reason are retained. The fresh suite used an enforcing
process preflight. The older USA menu stall is also retained; passing USA cases
here do not establish its root cause. Last fully passing seven-case suite remains
the earlier 50a checkpoint.

The [public proof](../../results/proof/2026-09-10-exotica-native-lifetimes/README.md)
recomputes source/file hashes, receipt consistency, capture coverage and stored
repeat identities. Actual native execution, Lua joins, raw pixels/resources,
build reconstruction and tests remain receipts. Raw game data stays local.

## Next rendering work

Validate the local allocated-waiting selector against the five independently
joined snapshots before native promotion. Bind eligible never-submitted objects
to allocation generation and source realm, preserve source order, and invalidate
on reuse/reset. Use current coherent object fields and independently checked
materials. Then verify live observation, insertion, original route and completed
4K output before judging fade/handover. Preserve intrinsic translucency and
foreground depth; object fade fields are not every quad's final alpha.
