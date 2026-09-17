# Mars stutter: bounded CPU phase timing

The existing attended drive is sufficient to investigate the stutter. No new
recording was requested. Two adaptive profiling replays used its recovered case,
with the original8089frames and120explicit scripted continuation frames.

`--exotica-timing FIRST:LAST` records at most2000frames of CPU scene phases.
Its bounded65536row buffer is allocated at startup and written only at exit.
Disabled mode collects nothing. Empty, interrupted, overflowing or malformed
captures do not pass. The recorder rejects accidental inheritance of this
diagnostic. Nested material phases are excluded from aggregate CPU totals.
This measures CPU work, not GPU execution time or physical input latency.

Native8b52a38fd52 first measured7780..7840. Its492rows showed geometry assembly
averaging2.04ms, while the broader material phase reached22.19ms. Native44388a202e1
then separated material staging, encoding, queue submission and commit. Staging
peaked at0.070ms and commit at0.262ms; queue submission peaked at20.824ms. At
native frame7818 a2.994MB geometry packet accounted for this wait. Submission
calls only the bounded graphics ring producer. A full ring waits for the
consumer, blocking the emulation thread. This explains a concrete source of
pauses; it does not establish that every user-reported steering interruption
has the same cause.

Both8209frame replays PASS, preserving inputs/time and all native images, with
four saved3840x2160 GL images exactly equal to the prior candidate. Queues drain,
workers join and the renderer remains active. The first pass informed the
second; neither was a broad suite or a rerun for analyzer changes. One native
buffer/bounds test and two Python option/receipt tests pass.

Local evidence: `results/diagnostics/exotica-mars-timing-20260916/profile` and
`material-profile`. Native exports265/266 are frozen/attested in that parent
directory. Both export scripts have already run. Current native is44388a202e1,
SHA256 `bef04e5c110207143bb20670d6fe606a7eece6a55faaa752f25cd392ab8fc3a1`.

Source audit found an avoidable load: CPU scene hashes and the GPU consumer's
polygon hash are computed even when their sole destination is a disabled
per-event journal. The next isolated optimization will suppress those diagnostic
calculations in quiet mode, retaining all material/resource validation and all
capture-mode hashes. Compare against this timing baseline and the saved pixels.
Personal installation/publicv0.5.0 remain unchanged.
