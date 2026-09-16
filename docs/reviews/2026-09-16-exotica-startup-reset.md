# Exotica: reset safely before the first pool transaction

The continuous renderer now accepts a machine reset while startup is still
pristine: no pool readiness, lifetime epoch, scene preparation, material
generation or earlier active reset. All existing phase-quiescence checks also
have to pass. It leaves the untriggered guest startup taps installed and lets
ordinary emulation perform the reset. There is no auxiliary work to abandon,
no GPU reseed and no fabricated scene completion.

Resets during bootstrap ownership, a pending scene, another reset or a degraded
renderer remain rejected. The existing active quiescent reset path is unchanged.
A separate startup-reset receipt records the zero-state boundary. The harness
ties it to the actual scheduled reset and the subsequent independently verified
first pool/scene proofs. Startup and active resets retain separate indexes and
proofs; a focused test covers their combination.

## Actual reproduction and successor

A new original-renderer case uses the Mars stimulus with reset requested at
replay frame90. The old e13 candidate fails at native89 with
'Exotica reset requires quiescent continuous renderer'. Its shutdown confirms
all pending/prepared/matched/requested/completed fields zero. The failed run is
retained as old-strict.

Frozen successor225c295d870 passes all5460 recorded inputs/time/native images.
The startup reset is recorded at89; actual guest pool and first scene complete
at1474. Afterward the renderer completes3935 scenes,2,448,968 future quads and
2537 marked model preparations with zero rejection. All2,335,451,688 queued bytes
drain and the graphics worker joins.

3651 camera samples and10,953 actual ADC reads/times match the original control.
Ten completed3840x2160 CRT images at500-frame intervals were compared:
500..4500 match exactly. Frame5000 changes47,434 pixels only in the left margin
(x1..268, y157..1065), with no new near-black pixels. Both5000 images were viewed:
the Mars drive, foreground car/traffic and HUD remain intact; additional left
scenery is visible. This is not a new temporal or all-course visual acceptance.

The first local report assembler expected the prefix-only comparison_scope
field, which a complete-case report does not have. That KeyError is retained
in qualified-initial-failure.json. The corrected qualified-v2.json reads the
validated case frame count. No game was rerun for this reporting correction.

The native reset test covers every pristine-state exclusion. Three focused
Python tests pass, including startup followed by active reset, mismatched
action/frame/state, missing completion and preserved independent proofs.
The previous7500-input active-reset artifacts revalidate exactly for ownership,
actions and proofs with the updated verifier; no active-reset game was repeated.

Native225c295d87085ee12f96b04ad09e51f2244a6e28 is frozen with build attestation,
SHA70298c41e6355933398ef0600fd2db96e93fb9312b649e8d7d8d4f20c1dc9fc1.
The261-patch export reconstructs eb5aedb7cc3388fea94b80bd1fd7cf20e815e5cb.
Local evidence: results/diagnostics/race-transitions-20260916/exotica-startup-reset
and startup-reset-active-regression.json. Export/build receipts remain under
world25-roads-20260914.

Next investigate reset ordering and explicit retirement for genuinely interrupted
work. A reset cannot simply clear queued owner records or label unfinished
phases complete. No deployment, release, hosted CI or physical FFB occurred.
Personal Stream Deck87d/publicv0.5.0 remain unchanged.
