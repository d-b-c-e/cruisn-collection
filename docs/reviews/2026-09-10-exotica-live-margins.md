# Exotica live margin candidate — September 10, 2026

The separate native candidate now connects the owned current-object capture to
the original command fence and a private depth buffer. This is a CLI-only
diagnostic. It keeps original far distance and does not change product defaults.
Live gameplay acceptance is in progress; the earlier offline repair does not
establish acceptance for this integration.

## First integration checks and retained failure

The disabled5ff control completes6000 recorded inputs and25 paired4K images,
matching accepted2eac. All4,191 camera samples,12,573 actual ADC read times, and
ten original command/model/material resources are identical.

The initial observe run fails the render watchdog at frame5080. Both captured
late scenes reconstruct independently:5072 has63 instances/522 quads;5080 has56
instances/160 quads. Their original color and depth remain unchanged, and the
complete camera/input-read trace matches. However, synchronous raw color/depth
file writes hold the GL consumer for1.274/1.487seconds. Only11 of13 scenes reach
the consumer; the harness correctly rejects the lost rendering state and missing
material generations. The failed run remains local and is not a visual pass.

Native`c9982f3e662b7932ff598741b797662faf4fa978` moves those owned snapshot bytes
to the existing bounded FIFO writer, with separate completion/failure receipts.
It uses at most512MiB/32 pending-or-in-flight requests. Only explicit offline
capture pacing can wait for capacity; no GL or game memory reaches the writer.
This is a separate native fix, frozen at`build/candidates/c9982f3e662/vunit.exe`,
SHA256`7bf0f3659ca4adc58d4d91914bec7e91710c141f5499c858ec68bde519297d40`.
The171-patch export reconstructs tree`ff66026f1203fb21df1b70ceb13a1d2e1cec6593`.

Its capture-only replay now completes all13 scenes/4,435 captured quads,26 owned
material generations and all requested files. The same25 images, route, actual
ADC times and ten original resources match2eac. Both late independent geometry
reconstructions pass again. Snapshot callbacks drop to139/130ms, including full
GPU readback and validation; this is diagnostic overhead, not ordinary drawing
cost. Drawing/repeat and broader acceptance are still in progress. The329-test
source identity below belongs to the pre-async checkpoint; final checks must be
renewed after this fix.

`--exotica-host-active off|observe|draw` requires an explicit candidate when
overridden, the bounded scene observer, private materials, and command-fence
observation. Absent settings preserve old recording behavior. Recorded settings
round-trip; disabling the parent observer removes the active setting as well.
All these runs require physical force output disabled.

At the four original list boundaries, the CPU owns each object's rendering
operands and culling inputs. At the actual original FIFO completion, it rechecks
membership, slot contents, camera, matrices, projection constants, programs and
default state. Actual original model submissions are excluded. Added geometry
uses current model bytes and owned palette colors. Unsupported D24/raster cases
exclude the whole instance and are counted explicitly.

A second, explicitly ordered material generation belongs to the same scene as
the earlier future-scene observation. Its owned XMD1 packet contains geometry
and material updates together. No queued work borrows guest RAM or live device
pointers. The same written-page image tracks both phases and can compare every
generation with a complete scan.

The GL consumer flushes original polygons, copies original D24 depth only in the
two margins, and draws through that private copy into the shared color texture.
The original depth remains untouched for subsequent original rendering. Original
shader material, blending and dither behavior are retained. Eight-vertex clipped
polygons produce complete triangle fans. Observe mode consumes the same captured
geometry and materials without drawing them.

Snapshot checks require byte-identical original depth, center, other-page and
outside-page color. Producer/consumer counts, generation order, palette ownership,
triangle fans and snapshot completion are independently checked in Python. A
separate snapshot reconstruction is still required to validate geometry itself;
these receipts alone cannot certify transparent foreground ordering or handover.

Native `5ff1f9f81329a2dabed6b454a74ebd90b94b0aec` is built separately and pushed.
Frozen `build/candidates/5ff1f9f8132/vunit.exe` has SHA256
`a88a0f8106e801e2440c117fcb07f3b2cd96ae7e3cc67563682d72ebe2211e00`.
The170-patch export reconstructs tree`9cffd3235432005bfebeeda47812cbb9ff84d468`.
The first compile failed on hexadecimal-address tokenization; that log is retained
and the arithmetic spacing is fixed in a separate native commit.

All329Python tests/no skips,45native tests and125local commands pass at source
identity`fa537af0216bc8e6bb6535b8e3ebe346e121616c251c4e9a2decc083c40aff0c`.
The next acceptance is disabled/observe/draw/repeat on the Amazon recording around
native5072/5080, followed by broader time/track coverage and seven default cases.
Compare the actual input sampling times and camera route, original command and
material resources, independent late geometry, and completed4K images.

No deployment or release. Native2eac retains the last seven-default acceptance;
the personal Stream Deck binary remains v0.5.0/SHA87d04de4. Raw model, texture,
RAM and image evidence stays local. General farther depth, alpha ordering and
the separate original texture-upload timing concern remain open.
