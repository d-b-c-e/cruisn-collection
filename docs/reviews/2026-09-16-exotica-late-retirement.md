# Exotica continuous fallback after the diagnostic window

The CPU submission and GPU receipt of private-renderer retirement both retained
a16000-frame limit. Continuous scene operation can run beyond that limit, so a
real future-assembly failure later in a session would fail the retirement queue
instead of returning to the original view. This was found during the machine-reset
source review, without manufacturing another whole-drive failure.

Both boundaries now use the same `exotica_runtime::retirement_frame` rule:
capture mode retains1..16000; continuous mode accepts nonzero representable
32-bit frame numbers. Diagnostic fault injection still ends at16000. Existing
FIFO emptiness, scene ownership, policy, physicalFFB0, ordered flushing and
presentation requirements remain intact. No successful scene changes rendering.

Validation covers16000/16001, one million, UINT32_MAX, zero and overflow in the
compiled runtime test. Four focused Python failure tests pass, including a
non-injected18000/18001 failure/retirement receipt that remains explicitly
degraded. A local MAME build succeeds. No new game run, timing measurement, reset
acceptance, or live post16000 recovery is claimed; earlier bounded retirement
behavior and its completed-image evidence remain the baseline.

Native commit `569549d9aee75a78c004c3ad78f99e68080229fd`, frozen SHA256
`e9c477fa7c575bf77e8c6d42f1a246e817fb03300744cf37e8cec28ee9227fb1`.
The255-patch series reconstructs tree `dd5e248097adfd6aea546517d4ed0e3f48de865e`.
Local evidence: `world25-roads-20260914/late-retirement-build.log` and
`late-retirement-native-export.json` under diagnostics. The personal installation
and publicv0.5.0 package are unchanged.

The machine-reset issue remains separate. It currently aborts once lifetime or
command-fence tracking begins. A reset can interrupt an unfinished CPU scene;
simply clearing those guards or calling the existing quiescent retirement path
would lose pending ownership. Reset requires an ordered GPU boundary, explicit
CPU cancellations, fresh material/endpoint ownership and verified guest startup.
MAME's Lua `manager.machine:soft_reset()` schedules the actual emulator reset;
screen frame numbers continue across it. No reset API or runtime behavior is
changed by this fix.
