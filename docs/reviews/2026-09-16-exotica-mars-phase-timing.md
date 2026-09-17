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

## Quiet-mode optimization

Native1fccd423f39 now omits five CPU journal-only hashes and the GPU worker's
per-polygon journal hash when capture is disabled. These hashes did not feed
rendering, admission, resource leases or summary integrity receipts. All of
those checks remain active. Capture-mode hashes remain unchanged, including the
first GPU packet whose journal opens lazily. V-Unit's separate rolling geometry
fingerprint is untouched because it does feed its quiet-mode receipts.

One subsequent replay (`quiet-hash-profile`) passes8209input/time frames, all136
native snapshots, and all four completed4K GL images at100.0000% pixel equality.
The continuous transaction and joined/drained shutdown checks pass. The existing
native capture/quiet journal contract passes. No broad game suite was repeated.
The first launch command accidentally selected MSYS Python after the compiler
PATH override and failed importing PIL before any game launched. Explicitly
selecting the regular Python runtime corrected the invocation; this did not
require another drive.

| Measure | Prior candidate | Quiet hash optimization |
| --- | ---: | ---: |
| Maximum future queue submission,7780..7840 |20.824ms|0.187ms|
| Mean future queue submission,61samples |1.114ms|0.101ms|
| Maximum callback interval,7780..7841 |35.683ms|18.850ms|
| Callback intervals above25ms in that62frame window |6|0|
| Callback intervals above25ms,3000..8079 |61|44|

This is one local pair with the same settings and profiling schedule, not a
multi-run benchmark or proof of physical wheel latency. Other spikes remain:
the maximum callback interval across3000..8079 was60.716ms before and66.329ms
after. Do not call all stutter eliminated. The repeatable late-route queue stall
has nevertheless been substantially reduced without changing the sampled output.

`compare_timings.py` and `timing-before-after-qualified.json` retain the exact
CSV/report identities, measurement windows and counts. Native267patches are
frozen/attested in `quiet-hash-native-export.json`; that export has already run.
Candidate SHA256 is
`5e56d183e2e59b79c0cb352fc8d260ddc7a1ed6a6a706a028b76e52ff30f2755`.
No deployment, publication, physical FFB or new attended recording was performed.
