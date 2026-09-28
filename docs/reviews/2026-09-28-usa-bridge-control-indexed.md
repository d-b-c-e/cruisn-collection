# USA Golden Gate: matched control indexed ownership at frame 10476

The [red-coverage screen](2026-09-28-usa-bridge-red-coverage.md) found
2,558 candidate-only red CRT center samples on newly covered host pixels,
while 2,304 other exact host samples already had the same index in an
*isolated* ordinary source raster. A matched control indexed mirror now
tests what actually reached the completed page, without inferring it solely
from source packets.

Frozen diagnostic native `f762e01d63b` replayed the saved USA Golden Gate
case through 10,480 inputs with ordinary continuous 3×, CRT on, literal
FFB0 and the physical 2560×1440 primary. Its raw report **PASS**es recorded
input/native comparison, display watch and owned worker shutdown. The
completed 10476 control BMP is byte-exact to the earlier matched
partial-coverage-off image. The existing detailed coverage-on run supplies
the candidate indexed mirror and a BMP byte-exact to the earlier on image.
Both visible-page original-only index/tag planes and the 4:3 indexed center
are exact between modes.

The candidate changes **7,058 indexed pixels**, all in the left widescreen
margin at x=45..183, y=792..1023 of the 2736×1600 page. Every changed
control pixel has ordinary game tag `1`; every candidate pixel has host tag
`5`. No center or right indexed pixel changes. This is an exact completed
ownership difference, not a count of red screenshot pixels or submitted
quads.

Inside the fixed far-left red CRT ROI, 4,906 candidate-only screenshot
centers map to unique indexed points. **2,558** have a changed completed
index/tag and trace to newly admitted source packets: 1,779 from object
`0x800a0040` and 779 from `0x800a0042`. The isolated ordinary host scene
has no coverage at those points. The other **2,348** red screenshot centers
have **identical completed index and tag in control and candidate**. Of
these, 2,304 also match exact existing candidate packets and the same
isolated ordinary host index; 44 do not pass the isolated host center-match
test. Their screenshot color difference is consistent with nearby changes
in CRT filtering or another presentation contribution. This check does not
assign a unique cause to those 2,348 colors.

The result sharpens the earlier bridge claim: the partial-coverage option
does bring additional geometry into the completed left margin, but the
4,906 red screenshot count overstates the amount of newly covered red
center-sampled geometry. The subsequent
[full indexed source check](2026-09-28-usa-bridge-full-indexed-source.md)
attributes all 7,058 changes to five newly admitted source objects at this
frame. One frame
does not establish a complete bridge silhouette, smooth handover, another
USA course, 4K, GPU pacing or release safety. The option remains diagnostic.

The reusable `harness/screen_usa_bridge_candidate_pixels.py` now accepts
`--control-mirror`, verifies case/binary/display/input/FFB/shutdown and exact
control image, checks original-only/center preservation, and emits source
hashes plus full-page and red-center ownership partitions. Python
compilation and source-hashed local report
`results/diagnostics/race-transitions-20260916/usa-bridge-candidate-pixels-v5.json`
**PASS**. The prior v1–v4 reports remain intact. The new control raw report
is `usa-bridge-control-mirror-10476-run/report.json`; its prepare-only plan
passed before gameplay. No native source/binary, deployed renderer, personal
installation or public release changed.
