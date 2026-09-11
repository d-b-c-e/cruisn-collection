# Exotica packet and allocation identity checkpoint

These receipts cover exact 2x/3x/repeat presentation after the bounded packet
serializer change, measured game speed, and original allocation-to-fade joins.
See the [review](../../../docs/reviews/2026-09-10-exotica-packet-and-identity.md).

Run `python results/proof/2026-09-10-exotica-packet-and-identity/verify.py` at the
source checkpoint recorded here. It recomputes source/file identities, capture
coverage and equality of saved hashes, and consistency of scalar receipts.
It does not rerun MAME, GPU rendering, raw geometry or fade reconstruction.
Raw game data and images remain local. Performance results do not establish full
speed or smooth frame pacing. Allocation matches do not establish material
lifetime or a host/original handover policy. No new default-suite, deployment,
release or physical-wheel acceptance is claimed.
