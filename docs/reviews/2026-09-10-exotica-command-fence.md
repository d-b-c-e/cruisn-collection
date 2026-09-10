# Exotica command completion candidate — September 10, 2026

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

Live acceptance is next: compare off/on/repeat, Hong Kong and full Amazon with
the original route, ordered geometry/materials/resources and completed4K images.
An independent Lua journal will bracket the target FIFO write with the first
following CPU instruction, and compare the native completion time with captured
original model execution. Then renew all seven defaults on the candidate.

This does not draw extra scenery. No new live completion or seven-default pass
is claimed yet. Personal Stream Deck stays v0.5.0/SHA87d04de4; last accepted live
defaults belong to7b432. No release, deployment, hosted workflow, physical FFB,
World force tuning or experiment removal. After acceptance, implement the private
depth target and margin drawing at the verified completion point.
