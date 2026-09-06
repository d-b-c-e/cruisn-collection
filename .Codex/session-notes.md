# Session Notes

- Date: 2026-09-06. Authorized all six improvements, separate commits, commit/push
  and fast-forward master after CI. Branch: codex/graphics-and-wheel-contracts.
- Primary new handoff: docs/reviews/2026-09-06-follow-through.md.
- Starting milestone: collection 5d61756, MAME eb4db8fc706, toolkit v0.10.1.
  Original assessment tags remain: collection d099c2f, MAME 58203bb1, toolkit
  4e99136 (assessment-2026-09-05). Original recordings were not modified.

## Implemented and verified

- MAME 368fab713ac on poc/quadlog; push only remote fork, never mamedev origin.
  Built E:/Source/mame-src/vunit.exe; racing deployed executable untouched.
- Ordered V-Unit quads/resource changes/CPU writes, persistent pages, completed
  visible-frame fences and process-private rings. Lossless queue backpressure
  in V-Unit and Zeus; 500 ms timeout abandons GL and diagnostics reject fallback.
- Retired default broad margin suppression/column stretching: it destroyed real
  World/Off Road skies. MIDV_GL_MARGINFILL=1 restores the legacy experiment.
  Local crack fill/default/radius unchanged. Thin terrain/near-tree seams remain.
- Toolkit v0.11.1 at b726d56, already pushed and CI green: native/managed bounded
  100 ms impact mixer, scalar source/quality/time contracts, strict managed wheel
  identity selection including negative-index rejection. Native device ABI and
  other consumer projects were not silently upgraded. 109 managed tests pass.
- Opt-in ffb_impact=1 / ffb_impact_<rom>=1 uses raw motor input for detection
  before driver adaptation, adapted input for structural force, common final
  strength. Compiled raw126/adapted20 test detects at 100 ms; legacy misses it.
  Host API acceptance logs are not physical force measurements. No wheel force
  was used unattended; physical subjective acceptance is still open.
- Explicit attended --record-with-ffb is permitted only for a real recording.
  Playback/synthetic/timeout diagnostics cannot enable physical force. Every new
  case has emulated-time force-source.csv and source-provenance signals.csv.
- USA v4.5 numeric displayed speed found at E632, formatter A7C2, renderer 7A91.
  Guarded foreground HUD submissions select numeric speed on the visible page,
  max age three frames; OCR fallback, MIDV_SPEED_NUMERIC=0 opt-out. This is HUD
  numeric MPH, not the game's physical velocity vector. Other games unchanged.
- Actual USA LOD transition traced at 8,000 units; explicit checked experiment
  raises 8,000/15,000 to 12,000/22,500 and adds 48 quads to one traffic car. File
  patch/game/crusnusa-lod-experiment.txt is NOT the default. Far plane unchanged.

## Evidence and limitations

- Tracked compact reports/images: results/proof/2026-09-06-follow-through/.
  Full runs remain gitignored in results/diagnostics/six-*; see review for paths.
- Final rebuilt candidate: six-final-raw-usa passes original human 5,012 frames /
  83 native images. six-final-raw-world25 and six-final-raw-offroad pass 6,000 /
  100 synthetic driving cases. six-final-raw-exotica passes 3,600 / 60 boot/attract
  case using recorded throttled settings. Exotica HEADLESS diverges after 1440;
  do not call this gameplay or exact GL coverage. World v2.4 also has driving
  coverage and 11 repeated GL frames. First Off Road neutral case is not driving.
- six-ordered-gl-identity and six-ordered-stall-identity: 31 consecutive USA GL
  frames equal, including 100 ms stall/16 MiB ring. six-stream-overflow-load is
  an EXPECTED FAIL from actual lost-stream fallback after 5-second loading stall.
- World2.5/Off Road sky A/B: 22 GL frames preserve core columns167..1112 at1280px;
  real margin sky returns. six-default-sky-identity checks rebuilt default equals
  explicit disabling. This does not certify all tracks or eliminate thin seams.
- USA visibility patch still changes guest history: first player velocity write
  at9680 and position addition90AB occur frame3063 vs3064. 20,001 input reads and
  1,921 timestep writes agree. Replacing baseline timer sequence does not fix it.
  Exact upstream state dependency remains open. No timer/physics hack shipped.
- Preserve my-drive original human INP and usa-widescreen-candidate-case
  separately. Patched/unpatched full runs are not gameplay-equivalent. Renderer
  changes must compare the same patched configuration and actual completed frames.
- Final offline USA force trace produces four candidates at52964,57228,70484,
  84728 ms; these are waveform events, not four labelled real contacts. Label
  emulated_ms coverage/windows via harness/collision_labels.py before claiming
  crash-detection recall. Candidate times alone cannot rate subjective FFB.
- 35 Python tests, nine GPU quality fixtures, native helper/adapter checks pass.
  Full101-commit MAME export reconstructs tree525325db1308874a60650ec54de3896eb6459b21.
  Export regenerated after all MAME commits; never hand-edit generated shaders.

## Next priorities

1. Human routes and labelled wall/car collisions, then attended wheel tuning.
2. Identify adjoining polygons and clipping/coverage for remaining thin terrain
   and World near-tree seams; do not broaden crack fill to conceal them.
3. Exotica gameplay case and completed-frame Zeus GL capture oracle.
4. Resolve USA visibility/guest-state dependency and measure optional LOD cost
   across routes. Decode model/residency behavior separately for each game.
5. Find guarded numeric/physics telemetry producers for the other games and
   adopt toolkit contracts per consumer with its own regression tests.

Commands and clock semantics are in docs/DIAGNOSTIC-REPLAY.md. Physical FFB must
remain disabled in any unattended run or timeout-capable test. Never hard-kill
an active-force session. Keep RESULTS.md append-only.
