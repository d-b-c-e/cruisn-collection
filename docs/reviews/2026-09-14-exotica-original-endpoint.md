# Exotica endpoint at the original model command

A private replacement at the original command position is now demonstrated for
seven sources previously included in the early future scene. This is a bounded
offline result and a standalone helper, not a live fade policy.

## Actual transition capture

The unchanged native0cc candidate replays the first5,260 Amazon inputs with
physical FFB disabled. Original native images pass;3,460 camera samples and10,380
actual ADC reads/times exactly match the accepted full run. All49,609 lifetime
records through5258 match that run's prefix.

The new original-only capture contains331 actual device models and3,280 ordered
quads in the consumer interval ending at5220. The bounded CPU collector records
8,365 calls/8,134 emissions over its requested5218–5252 window. Two later frames,
5244/5246, have no calls, causing the older full-window verifier to reject that
capture. That failure remains. An explicitly derived, byte-bound prefix5218–5243
has complete26-frame coverage and qualifies the first handover interval. The
later gaps are not silently treated as validated zero-draw frames.

Independent transform/setup/model reconstruction passes for that qualified
prefix. Of331 device models,236 have an unambiguous ordinary CPU call and233 have
consecutive original contexts. Seven model calls join through their actual native
lifetime generation and CPU emission to sources already admitted at5072. Their
original source-alpha values are8,16,16,48,96,152 and184. One is its first original
draw; the others are continuing fades. Unknown owners and an unavailable previous
context remain excluded.

## Completed-frame result

The complete original command replay matches native color and depth exactly.
Substituting the completed fade state for those seven models at their original
command indices changes66 of3,280 quads. Every vertex, material binding, unrelated
quad and other command remains unchanged.

The finished page changes3,830 RGB pixels and2,331 depth samples, with no new black
pixels. The other page and unused target rows remain exact. This is one completed
2736×1600 page, not a live4K or across-frame continuity result. It demonstrates
that the transition can be changed at its original placement without drawing a
second translucent copy over it.

## Standalone implementation

`native/exotica_model_endpoint.h` prepares original/replacement quads from owned
model bytes and the **current actual device context**. It first reconstructs an
unchanged control and requires exact original quads. It accepts only explicit
fade markers, the legacy renderer policy, unchanged program/palette/texture and
actual transforms. Replacement differences are limited to blend enablement,
source/destination coefficients and depth bias; vertex changes reject the whole
result. Failures leave the previous public result untouched.

The caller still must establish earlier admission, source/generation ownership,
the precise FIFO model boundary, current resources and one replacement at the
original command position. The helper cannot establish these itself and is not
linked or added to the MAME sync manifest. Its analyzer and native unit test are
included in the local check inventory.

Seven compiled actual-model cases match independent Python original/endpoint
bytes, and11 malformed/domain analyzer cases reject without producing output.
The native unit test covers original-control mismatch, wrong palette/program,
policy, geometry and transactional rejection. An initial missing test include
and a packed-versus-linear palette-address comparison were corrected before
qualification.

Two shortcuts were rejected or qualified explicitly. Forcing a fresh transform
from a preceding model did not reproduce the original model3. Using the current
actual device transform avoids that problem. Some endpoint source/destination
coefficients then differ from the preceding-context reconstruction solely on
nonblended quads. The raw byte-equality failures are retained. Both shaders ignore
those coefficients when blending is disabled; a separate completed GPU replay
confirms **entire color and depth buffers exactly equal** the preceding-context
endpoint. No bytes were normalized or hidden to obtain that result.

The first attempted capture configuration combined future drawing with a command
journal. The harness rejected that unsupported combination before launch. The
successful capture keeps the existing guard and records original commands only.

## Next integration boundary

The current device model callback occurs synchronously inside Zeus FIFO writes.
Existing scene-fence code identifies the game ring consumer atPC`0xb686`, using
`AR0`. Original model commits atPC`0x6970` expose their two-word packet and ending
ring pointer. The next investigation is an exact ring-pointer/packet join between
those boundaries, rather than relying solely on model base and translation.
That join must be observed and checked before enabling any replacement.

Local evidence under `results/diagnostics/exotica-amazon-20260909/` includes
`fade-handover-original5220-control`, `original-handover-check` (full-window
failure), `original-handover-qualified` (fresh-transform failure),
`original-handover-contextual`, `original-handover-render`,
`current-model-endpoint-*`, and `compiled-endpoint-actual`. Raw game data stays
local. The latest executable remains native0cc; source native21c has only the
previous offline-endpoint correction. Personal87d/publicv0.5.0 are unchanged.
No new MAME build, deployment, hosted CI, release or physical FFB was performed.
