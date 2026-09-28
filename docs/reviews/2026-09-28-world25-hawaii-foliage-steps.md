# World 2.5 Hawaii: foliage handover at one-frame cadence

The [five-frame-cadence Hawaii pair](2026-09-28-world25-hawaii-dense-transition.md)
showed a large left-margin foliage difference by completed frame 5775, but
could not locate its entrance. I replayed the saved World 2.5 drive over
completed frames 5768..5778 at one-frame cadence, changing only the active
non-road margin option between control and candidate. This is a bounded
transition screen, not a new renderer feature.

Frozen diagnostic native `f762e01d63b` and physical 2560×1440 display were
used with explicit CRT on, native height 400, 4× internal scale and literal
FFB0. Both 5,782-input reports **PASS** original input/native comparison,
display watch and owned worker shutdown. All eleven 2544×1353 completed
images are present. The new frame-5775 control and candidate BMPs are each
byte-identical to the corresponding earlier five-frame-cadence captures.
The paired report **PASS**es center-third preservation; every difference is
confined to a left or right margin. The 96,180 extra submitted quads over the
prefix measure work, not visible gain.

| Completed frames | Changed RGB pixels per frame | Where | Inspected transition |
| --- | ---: | --- | --- |
| 5768 | 1,959 | Right | Guardrail edge extends. |
| 5769–5770 | 673 | Left | Tiny foliage at outer edge. |
| 5771–5772 | 9,203 | Left | More foliage becomes visible beside the foreground tree. |
| 5773–5774 | 41,455 | 28,980 left; 12,475 right | Larger foliage area and separate guardrail continuation. |
| 5775–5776 | 24,339 | Left | Outer tree remains after the nearby foreground clears. |
| 5777–5778 | 11,863 | Left | Remaining outer foliage narrows as the camera turns. |

The game's visible scene changes about every two captured frames here. The
between-mode difference footprint grows by 9,121 locations at 5770→5771 and
39,797 at 5772→5773, then loses 28,158 at 5774→5775 while gaining 11,042
elsewhere. These are changes in *where the two modes differ*, not tracked
object areas. The inspected sequence is consistent with scenery emerging as
the nearby tree clears, and the candidate retains left-edge foliage where
control shows sky. It does not establish a fade or show that no object pops
when viewed continuously. The previously source-qualified 5775 ownership and
depth result applies to that frame only. The authored dark terrain rectangle
at 5900 is outside this interval and remains a separate open defect.

An initial matched 5,782-input pair also **PASS**ed, but its invocation omitted
the explicit CRT override and produced CRT-off images. Both mode arms were
internally matched, yet their 5775 BMPs differed from the earlier CRT-on
images across most of the screen. The CRT-off raw reports and paired/adjacent
analyses remain under `world25-5773-step-*`; they are not used as CRT-on
repeatability evidence. This was a diagnostic setup error, not demonstrated
gameplay divergence. The corrected `world25-5773-crt-*` reports, paired
comparison and adjacent-step analysis are the evidence for the table above.

To prevent the same omission from passing a default-view gate silently,
`harness/compare_world_nonroad_course.py` now accepts explicit required CRT,
GL-scale and native-height values and checks both raw invocation environments
before reading images. The corrected pair passes with CRT=1, scale=4 and
height=400 (`world25-5773-crt-paired-v2.json` records these requirements).
The earlier matched CRT-off pair fails that same gate with observed
`MIDV_GL_CRT=[None, None]`; its raw rejection is retained. Three focused
presentation-contract tests and Python compilation pass. The flags are
optional so intentionally raw-mode comparisons remain possible and honestly
labeled.

No native build, renderer deployment, personal Stream Deck installation or
public release changed. The interval is one World 2.5 course at physical
1440p without wheel force, and does not qualify 4K or other scenery types.
