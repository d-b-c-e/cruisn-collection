# Exotica shutdown state observation

A new explicit `--exotica-shutdown observe` option records actual ownership and
transport state at teardown. It requires an Exotica candidate, verified guest
scene startup, and physical FFB disabled. It changes neither exit timing nor
drain behavior.

The CPU receipt runs before the other diagnostic exit notifiers. It reports
pending pool/source/model/endpoint/fence/waiting/composition work and paired
preparation/completion totals. The GPU receipt distinguishes rendering/writer
errors from missed finite capture bounds. After joining the GPU thread, the
producer records the final written/read queue positions.

The Python verifier returns `quiescent`, `interrupted`, or `failed`. It rejects
missing, duplicate, malformed, overflowing or inconsistent receipts. It does not
turn an interrupted capture into a passing rendering result. Three focused tests
cover classifications, queue/counter bounds, and explicit configuration.

One short1,900-input startup prefix verifies the live observer. At frame1,899,
all510 prepared/matched scenes and requested/completed fences agree. Every CPU
pending flag is zero. GPU material and endpoint work is empty; no renderer or
writer error is reported. After the thread joins, written and read positions are
both124,279,648 bytes. The observed stop is quiescent, and all recorded inputs,
emulated times and original native images match.

The overall capture report intentionally remains FAIL: the declared lifetime
last frame is1,899, so its strict completion predicate is not satisfied at that
exit. No eligible early endpoint snapshot was expected either. The separate
observer/input qualification passes without weakening those capture rules.
This is not an active-race interruption test, continuous runtime acceptance, or
evidence that every exit is quiescent.

Initial compilation failed because the stop function referenced a helper local
to the GPU thread. A separate fix uses the environment lookup in the correct
scope; the failed build log remains. Frozen native `ede2c7a4ea7`, SHA256
`53c513b80572f733d4b1bc7157f8600de35eca66ffd52aa2dd24538a07b3180e`;
245patches reconstruct tree `ee699e1c987aee412e5c7cd2f3b329d06b12dc9d`.
Local evidence under `results/diagnostics/exotica-amazon-20260909`:
`shutdown-observer-prefix`, `shutdown-observer-prefix-qualified.json`, and
`shutdown-observer-native-export.json`. The export script already ran.

## Remaining runtime policy

Startup now has verified guest boundaries. The next implementation must treat
normal runtime and finite capture completion separately across CPU and GPU:

1. Keep source/lifetime/ticket/material ordering and live-resource bounds.
2. Give normal operation an explicit end policy; do not use an enlarged capture
   window as a substitute. CPU lifetime, scene, endpoint/admission and GPU mirror
   windows must agree. The material codec's remaining16001 upper bound must also
   become policy-specific.
3. Preserve strict capture-completion checks. A normal interrupted exit needs
   explicit pending-work reporting and joined resource teardown; it must not be
   relabeled a completed capture. Retiring the feature while the game continues
   remains different from destroying the entire emulator on exit.
4. Keep guest pool clears/rebuilds distinct from MAME machine reset. The latter
   still rejects after observation starts and requires a separate reset contract.
5. Use one justified multi-race recording when the runtime implementation is
   ready, covering menus, another track and normal exit. Do not repeat existing
   full drives just to produce more identical samples.

Personal Stream Deck executable and publicv0.5.0 remain unchanged. The latest
change only adds explicit diagnostics to the already qualified startup candidate.
