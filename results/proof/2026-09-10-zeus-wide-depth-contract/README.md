# Standalone Zeus wider-depth and future-packet contracts

Run `python verify.py`. This recomputes source identity, compares promotion hashes
and checks the hash-bound local/native/GPU receipts. Rerun the source tests for
actual GPU execution and native packet parsing. Raw captured game polygons and
the local synthetic native packet are not archived here; their comparisons are
receipts, not independently recomputed geometry from this archive.

No native MAME build, wider game image, frame ordering, material handover, live
performance or default-suite renewal belongs to this milestone. Native25228 and
personal v0.5.0 remain unchanged. The initial scalar-alpha reference failure stays
visible; final RGB/depth use the independent CPU oracle, and exact RGBA uses the
original material shader with independently decided depth admission.
