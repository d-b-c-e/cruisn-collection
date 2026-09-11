# Impact-source reachability receipts

Run `python results/proof/2026-09-11-ffb-impact-reachability/verify.py` to check
current code hashes and aggregate comparison consistency. The recorded tests ran
the old common-baseline analyzer and the new reporting-only analyzer on four
actual source traces, in both legacy and enhanced modes. All eight complete
stage CSVs and existing metrics match. Thirty-five new compiled synthetic cases
and six existing adapter/alias cases passed.

This command does not compile/run those binaries, load private motor traces,
reproduce the native game runs, reconstruct the real host worker or test a wheel.
Execution results are receipts. The source peak covers all motor writes; tick
metrics and event counts describe an idealized 4 ms loop and are not collision
labels. The earlier common-baseline receipts bind the previous analyzer source;
this checkpoint changes its reporting, without changing its force stages.

The enhanced Exotica Amazon source peak is below the detector's arrival threshold.
It cannot create an event in that path under current settings; strength does not
change this pre-strength recognition. No universal hardware-range, other-track,
legacy-rumble, new tuning or physical-delivery claim is made.

See [the findings](../../../docs/reviews/2026-09-11-ffb-impact-reachability.md).
LOCAL evidence: `ffb-exotica-impact-reachability` and
`ffb-impact-reachability-comparison` under the Amazon diagnostic directory.
