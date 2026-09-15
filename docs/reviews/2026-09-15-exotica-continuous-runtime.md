# Exotica continuous runtime policy

The combined renderer now has an explicit candidate-only
`--exotica-runtime continuous` policy. One Amazon replay proves that CPU scene
preparation and GPU mirroring continue beyond every supplied capture end, with
unchanged saved rendering output and a quiescent joined exit.

This removes a fixed-duration restriction from the experimental renderer. It
does not add farther geometry, establish multi-race acceptance, or promote the
candidate to the launcher or public release.

## Policy and evidence boundaries

Continuous mode requires the complete future/waiting/active renderer, marked
original endpoints, verified guest pool/scene startup, quiet journals, shutdown
observation and physical FFB disabled. CPU and GPU use the same canonical
selector. Missing requirements or malformed selections reject before gameplay.
Quiet execution preserves live source, ticket, packet, material and fence checks.

Finite capture remains the default. Its original start/end validation and
completion predicates remain unchanged. In continuous mode, the supplied finite
bounds remain reference and snapshot configuration; they no longer stop CPU
lifetimes, scene preparation, original endpoints/admissions or GPU mirroring.
Guest startup uses the actual verified transactions, without requiring them to
precede a recording-specific first frame. This is an explicit end policy, not a
larger capture window or a maximum-integer end sentinel.

Material packets retain the same layout and byte representation. An explicit
continuous frame policy accepts nonzero 32-bit frames beyond16001. Capture and
early-start capture retain their old upper limit. Native renderer frame
narrowing checks overflow instead of silently wrapping. Existing endpoint ID,
live occupancy, resource, ordering and packet-size checks remain in force.

Runtime acknowledgments explicitly identify `end=none completion=quiescence`.
Their transaction summaries qualify completed work at exit, not completion of a
finite recording window. The harness independently verifies CPU/GPU policy
agreement, last prepared/mirrored frames, startup proof and joined shutdown.
It rejects interrupted exits, render/writer errors, unfinished work, mismatched
counts and runtime receipts presented as finite capture. Runtime reports always
say `capture_completed=false`. An interrupted run remains available for
diagnosis; it is not accepted as passing parity.

## Targeted validation

- Two native checks pass: policy selection and interval/overflow boundaries;
  material retention and HMT/XWD/XMD packet round trips through frame16002,
  one million and the 32-bit wire boundary. Legacy-range packet bytes match.
- Twelve focused Python checks pass across runtime, bootstrap and journal
  verification. They include malformed/missing/duplicate policy receipts,
  interrupted exits, inconsistent progress, incomplete transactions and the
  prohibition against treating runtime as finite capture.
- One5,300-input Amazon replay uses reference ends5240/5241/5242. Last prepared
  scene frame5298 and completed mirrored frame5299 both exceed those ends.
- All3,850 prepared/matched scenes and requested/completed fences agree. All
  pending CPU/GPU fields are zero. After GPU join, written/read positions both
  equal5,074,092,384 bytes; there are no renderer/writer errors or ring drops.
- Original inputs, emulated timing and native images pass.193 saved camera/ADC,
  endpoint, geometry, resource and target files exactly match the earlier
  captured startup candidate. Four completed3840×2160 CRT images at5220,5224,
  5228 and5232 are byte-identical. These images precede the shortened end;
  the explicit final progress receipts and matched totals establish continuation
  beyond it. No post-boundary pixel comparison or performance gain is claimed.

Frozen native `e19b29ab09f`, SHA256
`91b9ebbdedcb3c84de1349bff157e872468e069a6734bce3b3003d1365540be1`.
246patches reconstruct tree `a0da315f1b42f82a16aa9ea98aa43eaac2208bff`.
Local evidence under `results/diagnostics/exotica-amazon-20260909`:
`continuous-runtime-4k`, `continuous-runtime-qualified.json`, and
`continuous-runtime-native-export.json`. The one-time export script already ran.

## Remaining acceptance

A two-race recording with the intervening menus is the next useful runtime
sample. A second, open-sightline track can also help find a visibly contributing
outer distance band; the existing Amazon snapshots should not be rerun merely
to seek a favorable distance result. Availability was requested from the user.

MAME machine reset remains explicitly unsupported after observation starts.
Verified in-game pool clears/rebuilds are a different operation. Feature
retirement while the game continues also retains its separate ordered fallback
contract. Ordinary interrupted emulator exit is observed, but is not yet an
accepted rendering qualification. No attended recording should begin without
the user's availability response.

The personal Stream Deck executable (`87d04de…`) and publicv0.5.0 are unchanged.
