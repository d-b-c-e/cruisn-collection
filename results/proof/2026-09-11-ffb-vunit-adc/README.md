# V-Unit steering sampling receipts

These receipts summarize independent reconstruction of ADC0844 steering values
on the accepted native795fc USA, World Germany and Off Road El Paso recordings.
The real bus reads are compared with INP at the reconstructed conversion time,
40 microseconds after the latest enabled command. The conversion callback itself
was not instrumented. No physical force or calibration acceptance is claimed.

Run `python results/proof/2026-09-11-ffb-vunit-adc/verify.py` to check the committed
code hashes and aggregate receipt consistency. This does **not** rerun MAME,
rebuild its native binary, read the private ADC journals/INPs, compare game pixels
or test a wheel. Native source digests and runtime results are execution receipts.
The Python test receipt includes the working tree's separate rendering drafts;
it does not establish their live rendering acceptance.

To reproduce the raw comparison, use the same frozen executable and original
private recorded case with `harness/replay.py --snapshot-mode raw --probe-script
harness/probes/vunit_adc.lua`, setting `CRUISN_VUNIT_ADC_LAST` to the complete
recording length. Then run `harness/vunit_adc_evidence.py RUN --rom ROM --output
NEW_DIRECTORY`. The analyzer requires physical FFB off, accepted input/native
pixel replay, the pinned executable, the exact bounded collector and its complete
receipt. Arbitrary probes or other native builds are rejected.

Raw game evidence stays in LOCAL diagnostic directories. The original USA
analysis rejection and the Off Road collector-budget failure are retained,
including the former analyzer's hash and the failed capture's identity.
