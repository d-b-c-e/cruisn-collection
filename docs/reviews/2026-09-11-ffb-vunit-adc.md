# V-Unit steering sampling for the strength-50 calibration

The input-sampling check now covers all four games. New full recorded replays of
USA, World Germany and Off Road El Paso verify **31,012 actual steering reads**
against recorded inputs at reconstructed ADC conversion times. Earlier Exotica
work verified another 7,060 direct steering reads. This closes a measurement gap
for the near-term normalization candidate; no force gains or deployed settings
changed.

## Measurements

All new runs use frozen native795fc, executable SHA256
`97cd738c6b89f59a7523c9494285c5ee625e9f5041622f542983d94173b37d7a`, with
physical FFB off. Original input times and native image comparisons pass.
Force-source, force-gate, speed-signal and drivetrain files match their previous
common-build baselines byte for byte.

| Game | Recorded input frames | Native images compared | Steering reads matched | Distinct steering conversions read | Reads differing from preceding frame snapshot |
|---|---:|---:|---:|---:|---:|
| USA | 5,012 | 83 | 4,569 | 4,569 | 3 |
| World Germany | 9,269 | 154 | 8,803 | 8,803 | 22 |
| Off Road El Paso | 9,644 | 160 | 17,640 | 8,820 | 122 |

Every difference from the preceding frame snapshot is one input byte. These
small sampling differences do not explain the large perceived force imbalance.
Off Road reads each sampled steering value twice in this capture. Repeated reads
are not independent driving observations and must not receive extra statistical
weight in calibration.

## What was verified

`harness/probes/vunit_adc.lua` observes original control writes, ADC commands and
CPU reads without reading the ADC itself or changing guest data. It records a
bounded event sequence and a completion receipt. `harness/vunit_adc_evidence.py`
independently folds the access flags, command restarts and latched results. It
uses the pinned ADC0844 contract: conversion finishes 40 microseconds after the
latest enabled command, at which time the selected input port is sampled.
USA returns the byte at bit 24; World and Off Road use bit 16.

The analyzer reconstructs the steering port from post-curve INP state at that
conversion time, using the previously verified interpolation and rounding. It
never reapplies the live steering curve. The conversion callback itself is not
instrumented: its schedule is reconstructed from observed commands and the
pinned native source, then checked against actual latched reads. Non-steering
channels receive latch-consistency checks, not independent input reconstruction.

Twelve-place timestamps retain uncertainty. The initial USA analyzer rejected a
control write tied with a conversion deadline. Inspection showed it changed
only access permissions, leaving the conversion timer and latch untouched; these
operations commute. The corrected fold defers conversion reconciliation until a
later unambiguous access. Actual reads or commands with ambiguous deadline order
still fail. Both the first analyzer and its rejection are retained.

Off Road exceeded the initial 131,072-event budget at frame 9008. That incomplete
capture and its 6,826,795-byte journal are retained. A fresh capture with an
explicit 196,608-event bound completes with 141,236 events. The verifier accepts
the exact earlier collector for the two previous successful captures; arbitrary
probe substitutions remain rejected. New collection defaults to the larger bound.

## Validation and next delivery step

All **405 Python tests pass, without skips**, including eight ADC tests covering
conversion-time sampling, restart/latch behavior, permission gates, duplicate
reads, deadline ambiguity, malformed transactions and source/receipt rejection.
The tested source identity is
`d71c28101e0e38e8a15a4a28f089bd3f381b80f1c530c43f05bfcd78667b7b07`.
No MAME rebuild or physical wheel output was needed for this work. These native
image comparisons do not constitute new 4K/CRT presentation acceptance.

Next prioritize **matched clean turns, labeled contacts and final output
conditioning**, then deliver the separately versioned strength-50 candidate.
Current USA remains the initial reference. The existing idealized 4 ms offline
analyzer does not reconstruct actual host-worker wakeups, coalesced writes,
asynchronous gates or device effects; its RMS is insufficient for selecting
gains. The next conditioning work should expose a device-free path with explicit
timing evidence. If existing footage cannot supply comparable left/right turns
and contacts, obtain short targeted drives rather than tuning unrelated segments.
This milestone does not wait for rendering-distance parity.

LOCAL evidence lives under `results/diagnostics/exotica-amazon-20260909/` in
`ffb-usa-adc`, `ffb-world-adc`, `ffb-offroad-adc-bounded`, `ffb-vunit-adc-final` and
`ffb-vunit-adc-python-checks-final`. The failed Off Road attempt is `ffb-offroad-adc`.
[Public receipts](../../results/proof/2026-09-11-ffb-vunit-adc/README.md) check code
hashes and reported-count consistency; raw game/input/pixel execution and physical
force acceptance remain separate.
