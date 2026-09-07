# Final portable-identity release evidence

Candidate source code 7cb6751, packaged commit be87237. Native 5bb965763b1 / 9D8
is unchanged from the preceding full runtime/graphics baseline. This directory
contains the renewed standard suite and exact-ZIP upgrade, bound to the corrected
source identity. Windows CI, Linux CI and the local checkout agree on every one
of 201 source input hashes. All 100 Python tests and four CI jobs pass.

The 174 completed GL comparisons in unchanged-native-full-gl.json are the earlier
binary-bound oldaa920/new9D8 runs, not newly relabelled source reports. Full paired
traces are retained in ../release-3720/runtime-traces.zip. No native renderer,
shader, runtime profile or graphics option changed during the metadata correction.

runtime-traces.zip contains final reports, frame/force CSVs, invocation/capture
receipts and logs, plus the exact local reproduction scripts. Copied install and
ROM directories are excluded. Each entry is hashed in runtime-hashes.json; all
proof files are hashed in proof-hashes.json. Original recordings remain unchanged.

The release gate remains NOT READY because human acceptance is pending. The
repository is also private and anonymous update checks return404; public hosting
requires a maintainer decision. No public release or physical FFB was triggered.

`attended-prepared.json` preattaches CI/package/upgrade receipts while leaving every
status pending. No human approval, driving observation or wheel feel is inferred.
