# Exotica reset: check ownership before child devices reset

MAME calls the driver's machine-reset hook after resetting its child devices.
Zeus2's device-reset hook already clears its FIFO word count. The prior guard
therefore did not establish that the FIFO was empty before reset, despite
checking that field. This was a real ordering defect in the acceptance boundary.

Native083ceb32407 moves the continuous renderer reset preparation into the root
device-reset hook, before child reset. It emits MIDZ_RESET_ENTRY with the actual
FIFO state before running the existing strict quiescence/pristine checks. It
does not cancel pending work or relax the guard. Initial frame-zero reset keeps
the ordinary path. The reset verifier now checks these optional receipts against
every scheduled action and requires each receipt before its startup/queued
transition. Older reports remain readable without claiming this newer proof.

## One existing active reset, unchanged presentation

The existing7500-input Mars reset completes with pre-device FIFO empty at5559.
Scene4161/material generation12372 and hash4cd5211dfa9ea853 match the earlier
accepted reset. Fresh pool and scene begin6944, with byte-identical proofs.
All original inputs/times/native images,5691camera rows and12921actual ADC rows
remain exact. All twelve completed3840x2160 CRT images5200..7400 are byte exact
the prior extended candidate.4679scenes complete and all2734357696queued bytes
drain with joined workers. No new ordinary-control run was needed.

Three focused Python tests pass, including missing/reordered/nonempty FIFO
receipts and a receipt appearing after its transition. The native build passes.
The first local aggregate report assumed the older report contained newer binary
attestation metadata and failed with KeyError. That failure is retained; the
corrected aggregate hashes the historical report and preserves the new attested
candidate. No game was rerun for this reporting error.

Evidence: race-transitions-20260916/exotica-active-reset/pre-device-3x/report.json
and pre-device-qualified-v2.json.262 patches reconstruct native tree
41b9e210b12310cbc370367d7555b7f71090f59f. Candidate SHA256
50779072342fb6046eb579e05a31e550b7526af87beab7805ffe467ca197f6d9.
Build/export receipt: world25-roads-20260914/pre-device-reset-native-export.json.

Interrupted bootstrap/CPU work and already-degraded resets remain strict/open.
This sample does not justify clearing queued ownership on those paths.
Next return to the visible-distance boundary: select an Off-Road view from the
existing positive2x/3x comparison before capturing any further opacity evidence.
The prior3360 scene had no visible opacity contribution and should not be repeated.

Personal Stream Deck87d/publicv0.5.0 unchanged. No deployment, release, hosted CI
or physical FFB testing.
