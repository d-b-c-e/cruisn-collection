# Off Road full-drive checkpoint

The attended El Paso drive exposed a final-section bookkeeping failure in the
experimental host renderer. The correction preserves the original route and the
successful prefix. Full 2x/3x and repeat receipts cover 66 display samples each.
See the [review](../../../docs/reviews/2026-09-10-offroad-full-drive.md).

Run `python results/proof/2026-09-10-offroad-full-drive/verify.py` at this source
checkpoint (source identity in `source-identity.json`). The verifier recomputes
source/file identities, frame coverage, equality/difference of recorded image
signatures, and consistency of test/build/route/scene receipts. It does **not**
rerun MAME, reconstruct raw geometry, compare original pixels or establish wheel
feel, broad-track acceptance or elimination of pop-in. Raw game data remains
local. The initial failed 3x run is retained separately from corrected results.

The 3824x2073 images are V-Unit client captures on the requested 3840x2160
monitor, with CRT enabled. The Stream Deck/public v0.5.0 build is unchanged.
The last clean seven-default suite still belongs to native50a; the later USA
menu-timing failure remains open. These are diagnostic candidates.
