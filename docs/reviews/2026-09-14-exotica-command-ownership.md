# Exact Exotica model ownership through the command ring

The recorded Amazon handover now has an exact CPU-commit to device-model join.
This removes the need to infer ownership from matching model addresses or poses.

On the unchanged native0cc candidate, the 5,260-input original-only replay passes
the original route and image controls. Its camera, ADC, lifetime journal, captured
device models and completed color/depth resources match the earlier control.

The bounded 5218–5222 collector records 22,403 FIFO writes. All 22,323 writes at
the known ring consumer PC `0xb686` match the consumed ring word and full write
mask. The other 80 direct writes remain explicitly separate. All 1,168 ordinary
model commits are consumed at their exact ending ring positions with matching
two-word packets. At most five commits are pending; none remain at the end.
All 331 captured device models join to their corresponding FIFO writes; 236 have
an ordinary CPU owner. The other 95 remain untracked. The seven previously
qualified fade handovers identify exactly the same CPU calls through this join.
No ring wrap occurred in this capture.

`native/exotica_command_owners.h` carries bounded, epoch-qualified tickets in
commit order. It rejects out-of-order consumption, packet mismatches, pending
pointer reuse, invalid domains and reset with outstanding commands without
mutating the queue. Its native tests include synthetic wrap and identical models
belonging to different owners. A compiled fold of all 23,492 actual reset,
commit and consumed-word operations exactly matches the independent Python fold.

The helper is not yet linked to MAME. Next is an explicit read-only native
observer: copy owned setup operands at commit, consume the exact ticket at the
device callback, and qualify endpoint preparation from current device state.
Earlier private visibility admission and an actual temporal replacement policy
remain separate work. This evidence does not enable a live fade fix.

Local evidence: `results/diagnostics/exotica-amazon-20260909/` contains
`fifo-handover5220`, `fifo-handover-qualified`, and
`compiled-command-owners-final`. An initial JSON report-writing failure and an
initial strict-compiler indentation failure remain in their earlier directories.
Neither affected the qualified results. No new build, deployment, physical FFB,
release or final4K acceptance was performed.
