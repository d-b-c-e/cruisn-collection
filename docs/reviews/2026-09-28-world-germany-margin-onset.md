# Germany left-margin appearance — September 28

The World 2.4 Germany cross-course check previously sampled four completed
frames at 7280–7340: the active non-road margin option added a small distant
building at 7280, while the other three frames were exact. A bounded matched
replay now samples the earlier 7200–7280 interval every ten frames to see
whether the option's visible gain exists before that one endpoint.

Both runs use the same saved Germany drive and frozen `f762e01d63b` native
binary on the stable physical 2560×1440 primary display, with literal FFB0.
Each passes 7,290 recorded inputs, original native comparison, display watch
and owned shutdown. The opt-in path submits 142,640 extra host quads across
2,807 scenes. All nine completed 2544×1353 images change **only in the left
third**; the middle third is exact. Pixel differences range from 1,762 to
13,727 per frame, totaling 67,482 frame-pixels. Thus the 7280 result was not
the candidate's only visible contribution in this turn.

The inspected contact and full-size views show distant left-edge scenery
present throughout the sampled interval, with the cabin/building most obvious
at 7280. The images do not establish that the same object remains visible
continuously: the changing camera can bring different edge objects into view,
and ten-frame sampling can miss a brief pop. The building's abrupt visibility
at 7280 may be an edge-of-view reveal rather than a distance cutoff. This is
cross-course appearance and center-preservation evidence, not a demonstrated
fix for Germany's reported black road textures or mountain/tree pop-in. The
completed-image comparator correctly returns **FAIL** for exact equality;
the route/preservation comparator passes. A near-black color heuristic counts
93 candidate-new and four recovered frame-pixels, but neither count is a
texture-defect classifier.

The initial invocation with an outdated Germany case path failed before
launch and is retained as `germany-onset-control-run/report.json`. The
corrected control and candidate reports are `germany-onset-control-run-v2` and
`germany-onset-nonroads-run` under the local
`results/diagnostics/world-new-york-20260927-live-1` directory. The paired
source-hashed report is `germany-onset-paired-v1.json`, the expected
exact-difference report `germany-onset-gl-v1.json`, and the review image
`germany-onset-contact.png`. No native code, release, deployed renderer or
personal installation changed.
