# Exotica fade and performance receipts

Run `python results/proof/2026-09-10-exotica-fade-performance/verify_archive.py`.
The verifier checks archive hashes and declared receipt consistency. It does not
rerun MAME, raw fade writes, geometry, images, native builds or GPU checks.
Those checks require the retained local game recordings and resource captures.

The archive records six full Amazon performance runs, original camera/ADC timing,
fresh Hong Kong/Amazon canonical fade probes and controls, final independent
native/Python fade verification, source identity and the complete local suite.
Performance is below full speed at 2× and 3×. Repeated model-format validation
caching had no consistent offline benefit and was not promoted.

The first summaries' cumulative mirror timer interpretation, initial missing
analyzer runtime and truncated-input bug are retained explicitly. Native MAME
and personal v0.5.0 are unchanged. This is no handover, material-lifetime,
full-speed, seven-default renewal or four-game parity acceptance.

See [the review](../../../docs/reviews/2026-09-10-exotica-fade-and-performance.md).
