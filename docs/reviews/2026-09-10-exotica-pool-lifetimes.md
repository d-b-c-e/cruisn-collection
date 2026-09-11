# Exotica scenery allocation lifetimes

The Amazon drive now has a verified allocation lifetime for its observed scenery
objects. A RAM address alone was insufficient: the original game repeatedly
reuses slots and rebuilds the entire pool after the race. This checkpoint closes
that identity gap for the recorded interval. It does not implement host fading.

## What was measured

A bounded, read-only probe follows the common allocator, removal routine and
pool reset on unchanged native `9ed`. It checks paired head/count changes,
original linked-list operands, instruction signatures and the complete reset
chain. An independent Python fold reconstructs slot generations and joins them
to the previously captured section allocation and fade events.

The complete Amazon run and repeat each contain 48,481 transitions: 24,693
allocations, 23,787 removals and one post-race reset. The independent join checks
all 4,018 section allocations and 2,539 sampled fades, covering 116 faded
generations. It observes 23,757 reuses, and explicitly distinguishes 26 removals
whose allocations precede the capture window. The reset invalidates 882 known
live generations. All six pool, section and fade trace/receipt files repeat
byte-for-byte, including emulated timestamps.

Both runs preserve 8,860 input frames, 7,060 camera samples and 21,180 actual ADC
reads and their timestamps. Their 21 completed 3840×2160/CRT images match the
original fade control exactly. These are limited capture windows, not full-drive
pixel coverage. Automated physical force feedback is zero.

## Original reset semantics and retained failures

The common pool uses head `10A8` and available counter `10A9`. Normal allocation
and removal update the head before the counter; the post-race rebuild writes the
counter first. The probe must recognize that transaction explicitly.

The original rebuild has an available counter of 1,200, but links 1,201 nodes
including its final null-terminated node. Disassembly and MAME's C3x repeat-loop
semantics explain the distinction: a repeat counter of 1,199 executes 1,200
link-writing iterations, followed by the tail write. The observer preserves
these original semantics rather than changing the game to match an assumption.

Two diagnostic failures remain available locally. The first exhausted its
40,000-event budget at frame 5,888. The second, with an explicit 131,072-event
bound, stopped after 48,430 transitions because it did not yet recognize the
count-first reset. The successful trace reproduces both earlier event prefixes
exactly. The corrected observer checks every rebuilt link, the actual tail,
head and count, and the reset's bounded duration. The independent fold requires
exactly 1,201 nodes. A fresh repeat also uses that exact count in the collector.

## Consequence for extended scenery

The future descriptor key must include track/bank, section and source. Once the
game allocates it, continuation must additionally match a live pool generation.
Removal invalidates that generation; reset invalidates the whole pool epoch.
Neither a matching address nor a matching source definition proves that a
previous object still owns the slot or its material resources.

Allocation also does not prove that the object has actually been drawn. The
next experiment records first original model submission, temporal-fade
submissions and the transition out of that fade, joined independently to these
lifetimes. Only then can a private host continuation be retired without an
unintended gap or second fade-in. Texture/palette ownership, intrinsic
transparency, foreground depth and original command ordering remain separate
requirements. No policy should make every distant object opaque indiscriminately.

Raw disassembly, pool data and probes remain local under
`results/diagnostics/exotica-amazon-20260909`. The
[public checkpoint](../../results/proof/2026-09-10-exotica-pool-lifetimes/README.md)
recomputes source/file identity, capture coverage, saved hash equality and
scalar-receipt consistency. It does not rerun raw lifetime reconstruction, MAME
or pixel comparisons. The retained failures are identified by hashes and
bounded receipts.

Native `583`, the personal Stream Deck build and public v0.5.0 are unchanged.
The latest source checks remain 352 Python tests without skips, 48 native
programs and 136 commands at the 510-file source identity
`6c2c6e3f99c291f00912158a028ccda89f4272b05c86941b14f7f73a886cd315`.
Only documentation, proof receipts and local diagnostics changed for this
checkpoint. No deployment, other-track, default-game or physical-wheel
acceptance is implied.
