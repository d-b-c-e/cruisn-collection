# World force rollback evidence

Native b9bef299f6d, SHA256
`093abbeb01ac779dbc81b734bea609a9a358eebc17a7cfbf2ad6002e017135af`.
Source identity: `b1994a10b473c7ce0eaffdc765464f280031372d43361d2535c0a8726c7ba723`.

World's recent driving-state force gate is removed; no strength adjustment was
made. The user's later instruction cancelled the proposed10% boost. Normalization
and oscillation remain known issues. Exotica's independent trim/gate are unchanged.

`derived-evidence.zip` contains33 derived reports, CSV/UDP traces, analyzers,
CI/test receipts and the native rollback-patch check. Each entry's exact hash is
recorded in `report.json`; archive SHA256:
`a016f0e66ab81865733319ec2ec78ebc507556c625bb68ebf9f54e5cd665a704`.
No ROM, RAM dump, NVRAM or personal configuration is included. Original input and
image fixtures remain local; replay reports retain their comparisons.

Both complete headless World replays pass native inputs/images, independent
drivetrain probes and actual UDP checks. All8803 Germany and5534 World2.5 force
writes remain enabled. Raw/adapted motor-source CSVs are identical to the previous
verified runs. Menu/race-end requests are forwarded again, without changing their
values. No physical force or renewed wheel-feel/release acceptance is claimed.
114Python tests and all four CI34186139718 jobs pass.

After extracting the archive, its `analyzers/analyze_force_gate.py` accepts the
case's `run` directory, `--memory` CSV, `--game crusnwld24` or `crusnwld`,
`--policy passthrough` and `--output` JSON to recompute the force verdict.
The archived drivetrain analyzer likewise accepts `run`, `--memory` and `--output`.
