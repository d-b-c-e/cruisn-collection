# Live original-command replacement in the private extended target

Exotica now has a gated live path that replaces qualified original model quads
only in the private extended target. The normal target receives the original
quad once; the private target receives its endpoint once, at the same command
position with the existing material bindings. Neither target receives both.

`--exotica-model-endpoint draw` requires an explicit candidate, physicalFFB0,
surrounding lifetime observation and actual private draw admission. It is a
bounded diagnostic, not a launcher setting or release default. Original guest
state, model execution, WaveRAM and palette uploads remain unchanged.

## Transfer and ordering

The producer verifies every actual original quad against its prepared control,
then sends a544-byte side record containing the original/replacement pair.
Original native capture still receives its unchanged ordinary record. The
consumer requires the immediately following original quad to match exactly,
checks model/index/count order, and splits the two target submissions. Missing,
extra, reordered or altered quads reject; an incomplete model cannot cross a
completed-frame boundary. Changes are limited to source/destination alpha,
the blend-enable bit and depth bias. Vertices and other render state must match.

The standalone pair test covers encoding, geometry/state corruption, duplicate
or missing consumption and frame conventions. All98 actual saved quads from11
models round-trip and consume byte exactly in both captured-frame and explicit
live-zero-frame representations. Seven harness tests include exact GPU receipt
ordering and mandatory private admission.

## First live result

Native `156a03abfb0` is frozen separately, SHA256
`b14d1d4b1ec2e58c8fa939d777e9c145a9ed2ce0a2a4b7e45c787806987095b6`.
The204-patch export reconstructs tree
`a8e191784a200556223198804078c6c463178fbe`; native is pushed to the fork.

The5,260-input Amazon prefix passes. Across5218–5222, all509 quads of58 admitted
marked models reach the consumer exactly once and in order. The original route,
camera/ADC/lifetimes, model commands/resources, original color/depth targets,
admission journal and all saved endpoint bytes match the prior observer control.
The saved future/waiting packet bytes also match; no early geometry changed.
The5072 private before/after buffers remain exact, before replacement activation.

Completed private frame5219 changes15,838 RGB pixels on page400; page0 stays exact.
Frame5220 changes15,222 pixels on page0 and retains the preceding page400 changes.
No new black pixels appear in either sample. Depths remain finite and in range;
unused rows stay exact. Visual inspection shows stronger distant foliage near the
road; the car, water, elephants, background and HUD appear intact in these samples.
This is the existing non4K display with2736×4096 internal storage, not a renewed
final4K acceptance or a complete temporal comparison.

## Next visual work

This establishes the handover mechanism. The early future/waiting draws still
use their old fade state, so this alone is not a complete early-visibility fix.
Next connect earlier private visibility to the original replacement over a
continuous bounded interval, preserving intrinsic transparency and the active
margin path's ownership. Then choose and inspect an appearance fade policy;
measure sustained performance after correctness. The current per-quad target
split deliberately favors diagnostic clarity over final batching efficiency.
Sharp-turn black margins and overall release parity remain open.

Local evidence: `results/diagnostics/exotica-amazon-20260909/private-endpoints5220`,
`private-endpoints-qualified`, `endpoint-pairs-actual`, and
`private-endpoints-export.json`. Personal87d, publicv0.5.0, FFB and launcher
settings are unchanged. No deployment, release, hosted CI or physical FFB.
