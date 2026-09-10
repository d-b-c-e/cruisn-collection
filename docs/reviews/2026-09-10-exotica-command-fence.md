# Exotica command completion acceptance — September 10, 2026

`--exotica-host-fence observe|off` adds an explicit diagnostic to the existing
host-scene observer. It watches the original ring consumer after Zeus processes
each FIFO word. The ordinary CPU scene-end marker supplies the target producer
pointer. Completion requires consuming every outstanding word in order and
finishing a complete Zeus command. An already drained ring completes immediately
only if the parser is empty. No word is inserted and no consumer waits for a
future command. This is intended to cover special commands as well as ordinary
models, without matching a final model by appearance or address.

The standalone ring helper tests wrap, wrong-order rejection, partial-command
rejection and every start/target combination in a small ring. The live diagnostic
checks the known C32 drain instructions, zero CPU-cycle delta, bounded completion
time and one completion per observed scene. Crossing a machine reset is explicitly
unsupported during this diagnostic. It relies on the game's existing ring not
overrunning; the observer does not change its producer or consumer.

Native current-object helper commit664cc49982c and fence commit
`2eac1821916bf4f2f7975b48b45c2e48da993a15` are separately reviewable and pushed.
The separately built candidate is frozen at `build/candidates/2eac1821916/vunit.exe`,
SHA256 `cef7160a13440afaf8b865a9ee1421d10cfad1fe6143bdb89a21a8b9a0174b63`.
The168-patch export reconstructs tree`8ef72024cfc4a3c52426f9942b7fec2aca5f0643`.
All324Python tests/no skips,43native tests and120local commands pass at source
identity`1d8f3f56d4e0ab85538b23c3187fb833a4150f5453ec27db294e23a7fc121b4a`.

Six comparisons now pass: Amazon off/on/repeat, Hong Kong, and full Amazon with
a repeat. They preserve330 paired completed4K images, original motion/actual ADC
times, ten original capture resources, ordered host geometry and sampled private
GPU materials. Short drives preserve4,191 camera samples/12,573 actual ADC times;
each full Amazon drive preserves7,060/21,180. Native17,951 scene completions pass
word order, ring wrap, parser completion, timing and zero guest-cycle checks.
Of those,5,771 were already drained at CPU ordinary_end.

The independent Lua journal checks69 scenes and1,101 pending FIFO words. Native
completion falls at the target write, bracketed by the first following CPU
instruction. Five captured last-model identities match the pending completion
or the last actual model before an already-drained CPU end. The initial Hong Kong
postcheck wrongly demanded that an already-completed model execute again at CPU
end; this failed result is retained. Its corrected branch separately verifies
the drained case. Completed emulator runs were reused with unchanged plan/probe
hashes; this required no emulator or runtime-source change.

All seven defaults now pass on2eac, including actual UDP/memory telemetry,
four software force-policy/polarity checks and21 completed Exotica4K captures.
The test source identity remains the324Python/43native/120command identity above.
The public proof at `results/proof/2026-09-10-exotica-command-fence` recomputes
all native completion clocks and sanitized independent cursor ordering. Raw game
commands, geometry, textures and images remain local; their comparisons, native
build, GPU tests and default checks are hash-bound receipts.

This does not draw extra scenery. Personal Stream Deck stays v0.5.0/SHA87d04de4.
No release, deployment, hosted workflow, physical FFB, World force tuning or
experiment removal. Next, test a separate original-D24 depth copy and margin-only
drawing at this verified completion point. This first diagnostic retains original
depth range; general3x far depth, transparent occlusion and handover remain open.
