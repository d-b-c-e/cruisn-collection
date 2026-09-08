# Exotica force polarity evidence

Native97600e9597e, executable SHA256
`b5ba0021a51a1f9ec50e105dde9c8112cb3c7e4ce71009ce4294841296383ee2`.
Source identity: `f5e07b106c6ead459bd2ffe5746bfa357005fe76aea40650266c013c83dfc3c7`.

The actual Exotica cabinet DIP now determines game motor polarity, separately from
steering and device direction. Strength and World behavior remain unchanged.

`derived-evidence.zip` contains42 indexed files. `report.json` records each exact
entry hash and the archive hash. It includes new no-force replay traces, analyzers,
CI/test/patch receipts, the prior user's attended force logs, and the failed initial
replay that ended at1052 frames before GL capture. No ROMs, RAM/NVRAM dumps or personal
configuration files are included. Original drives and screenshots remain local.

The completed Exotica rerun passes6000 inputs and21 completed GL images. All4616
force samples agree with the recorded DIP;2082 nonzero levels reverse sign with
identical magnitude and unchanged raw/adapted source. World control passes6000/100
and retains all5534 prior force requests. 115Python/native tests and4CI jobs pass.
Physical centering still requires an attended check. Prior attended logs are
identified separately; automated tests never actuated a wheel.

After extraction, use the included `analyzers/analyze_force_gate.py` with the case's
`run` directory, `--memory run/drivetrain-memory.csv`, `--game crusnexo` or `crusnwld`,
`--check-polarity`, `--output REPORT`, and `--policy passthrough` for the World control.
The output can be compared to the archived report. No emulator or ROM is needed
to recompute force polarity from these traces; a replay report alone does not
recreate its input/image comparisons without the original local fixtures.
