# Exotica outer-distance appearance screen

The saved Hong Kong frame5000 contains371 future instances in the first distance
band and419 in the second, but none beyond2×. Its successful extended-rendering
comparison therefore does not demonstrate a benefit from3× over2×.

Five saved scenes were checked independently against source radii, camera depth
and serialized admission bands. Amazon5644 has356 instances in the third band;
7187 has359. Within the outer tenth of the3× sphere-admission range,82 and162
objects respectively have projected boxes intersecting the screen. All82 at5644
and149 of162 at7187 carry the game's marked fade. None of these outer objects
uses an unmarked intrinsic blend. Projected boxes are conservative bounds, not
proof of visible pixels or measured first-appearance times.

For7187, the existing ordered GPU interval7188 supplies an independent CPU-model
join at command index32. Three offline renders preserve the original command,
material-update and depth-clear order: original future fades, completed marked
future fades, and completed fades with the162 outer objects removed. Removing
those objects removes1157 quads. All three completed color and depth buffers are
byte-identical to the original capture. The original later scene covers this
future-only contribution, so fading it cannot improve this particular frame.

This is a bounded diagnostic using the older saved original stream. It does not
reconstruct the current waiting/active composition or private original-command
replacements, and must not be presented as evidence that those paths have no
benefit. It also does not resolve5644, where larger outer objects may matter.

A future fade policy must remain continuous through source allocation and
original handover, including objects whose original marked fade has already
completed. Applying opacity only to marked future objects risks a jump when
ownership changes. No new fade policy has been implemented or promoted.

Local evidence: `far-appearance-screen/report.json` and
`far-appearance-completed7187/report.json` under
`results/diagnostics/exotica-amazon-20260909`. Three offline renders; no new game
or native build was needed for this screen. The next acceptance work renews the
combined temporal and known margin checks at4K on the current candidate.
