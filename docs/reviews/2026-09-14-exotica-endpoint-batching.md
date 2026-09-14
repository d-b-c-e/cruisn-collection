# Exotica endpoint batching: correct pixels, no demonstrated speed gain

The bounded GPU batching candidate preserves the checked output and reduces
forced target submissions by 91.5%. It did **not** improve measured end-to-end
speed in the first matched drive. Keep native `080f78a2358` as the accepted
pre-batching baseline; do not promote batching as a performance fix.

Native `81366bffadc19a2d38eaf7c96f968b0f846009b0` is separately frozen, executable
SHA-256 `b7e23898ed1f38775e0e2421aeda06f85b51cef3642ca1e47725577091530854`.
The 210-patch export reconstructs tree `44ba27780f4a7fdbfc96f9c549f281981f81b4b5`.
No personal executable, release defaults or public package changed.

## Behavior and evidence

Consecutive original/replacement pairs accumulate up to 128 entries. Each
target receives only its own version in the original order. The consumer drains
at model ends, ordinary quads, resource changes, sky copies, private passes,
presentation and input-chunk boundaries. Existing exact pair matching remains.

The full Amazon execution retains all 8,860 inputs, 30,308 accepted marked model
preparations and zero rejections. All 282,036 GPU pair records are byte-exact
against the pre-batching candidate. Original command identities, camera, ADC,
lifetimes, admissions, early geometry and saved original/private completed pages
5,073/5,645 also match. All fifteen completed 3440×1440 CRT bitmap files at
6,536–6,550 are byte-exact. The consumer reports 23,943 groups, maximum 98 pairs,
and none remaining: 47,886 forced target flushes instead of 564,072.

The original harness report failed because the batch announcement used stdout
and the completion receipt used stderr. The canonical checker now reads both
captured streams with a size bound and rejects duplicate, incomplete or invalid
accounting. Eleven focused endpoint tests pass, including split-stream receipts.
No game was rerun for this checker correction. The initial local recheck also
failed by expecting display validation already to exist in the interrupted
report; the corrected recheck explicitly performs the remaining display, input,
image, disabled-worker and stall checks. Both failures remain available.

## Performance result

One comparison with the same diagnostics and display, outside the selected
capture intervals:

| Native frames | Pre-batching speed | Batched speed |
| --- | ---: | ---: |
| 3,501–5,000 | 97.13% | 95.73% |
| 5,701–6,400 | 85.86% | 81.46% |
| 7,001–8,848 | 92.24% | 90.99% |

These instrumented timings include host scheduling and possible asynchronous
capture costs; one pair does not establish a stable regression magnitude.
Nevertheless, there is no speed gain to promote. Avoid repeated full drives
merely to seek a favorable result. Profile saved-scene CPU preparation next,
and gate or revert batching before carrying another candidate forward by default.
Full-speed 4K and broader four-game parity remain open.

Local evidence under `results/diagnostics/exotica-amazon-20260909`:
`full-batched-endpoint`, `full-batched-endpoint-rechecked-v2.json`,
`full-batched-endpoint-qualified`, `batched-endpoint-cost.json`, and
`batched-endpoint-export.json`. Raw game resources remain local.
