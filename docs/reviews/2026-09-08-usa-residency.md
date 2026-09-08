# USA pending scenery — 2026-09-08

The read-only follow-up establishes a concrete global experiment to try. USA
already holds pending objects beyond its 75,000-unit admission window. During
frames 2500–4300 of the LA Freeway-derived drive, 22,713 pending visits pass the
distance comparison at 2× but fail it at the current limit. Of those, 17,382 also
fit within 1.25×. These are repeated visits, not distinct newly visible objects.

`lua/usa_residency.lua` independently guards the actual admission/removal code,
observes its depth/flag writes and returns no replacement values. It records
66,234 pending visits, 1,169 activations and 1,366 deactivations. Maximum measured
pending depth minus radius is 117,026. `analyze_usa_residency.py` recomputes the
eligible visit counts. A 4,305-frame replay with native `dae2569f793` matches all
original inputs and native reference images; physical force is disabled.

The depth write at `72AF` executes in a conditional branch delay slot. Accordingly,
the trace includes behind-camera visits too; it must not be described as 66,234
far-plane rejection tests. The newly eligible far visits are ahead of the camera
and cannot belong to that near rejection. Activations are still guest work.

Next: test a guarded shared admission/removal extension (`727D`:75,000,
`727E`:80,000) together with the renderer far limit (`55`:80,000) and a host-owned
reciprocal tail. Enumerate/guard USA's vertex consumers first. Do not write the
tail over adjacent game RAM, grow model allowlists, or assume that existing
pending geometry proves resource/texture/order safety after activation. Preserve
the old drive and require candidate repeatability, completed GL and timing.

Evidence: `results/diagnostics/usa-residency-20260908`; derived CSV, analyzer,
probe, invocation and replay receipt are retained with the World 2.5 checkpoint
archive. This probe changes no product behavior, settings or FFB.
