# Local builds, checks and release uploads

Effective 2026-09-08: development and release builds run on the maintainer's PC.
Both GitHub workflows are disabled. Neither pushes, PRs nor tags start hosted
jobs. Do not enable or dispatch the manual hosted fallbacks without a new
maintainer request. The MAME fork currently has no Actions workflows.

## Separate personal and release targets

```powershell
# Build a fresh candidate package with factory defaults; leave the Stream Deck copy alone.
./build_local.ps1 -Target Release -Version dev

# Explicitly deploy a compiled native build to the personal Stream Deck copy.
./build_local.ps1 -Target Personal
```

Both compile incrementally with MAME's `SEPARATE_BIN=1`, writing
`mame-src/build/mingw-gcc/bin/x64/Release/vunit.exe`. The Release target freezes
launcher/setup into a fresh `build/release/CruisnCollection` and creates a dated
ZIP. It reads tracked fixtures and declared media, never the personal `rig/`,
cheat database, bindings, calibration or user force profile. Factory CRT, full
widescreen, scale4, World2.4, 50% force and CRISP profile are checked inside the
frozen executable. Packaging rejects personal config/profile/runtime files.

The Personal target copies only the compiled emulator to `mame-src/vunit.exe`,
keeping a hash-named backup under `build/personal/previous/`. It refuses deployment
while that game is running and does not change settings. Stream Deck continues
to launch the source checkout, so Python updates take effect when its launcher
is reopened. The two targets share code and compiler settings; personal preferences
are runtime files, not alternate compiled defaults.

Use `-SkipNativeBuild` to stage/deploy the already compiled separate candidate;
it is an explicit request to reuse that binary, not a freshness check. `-MameRoot`,
`-MsysRoot` and `-Jobs` override this PC's paths/concurrency. Neither target uploads
a release or runs GitHub Actions. `make_release.ps1` also accepts `-Emulator` and
`-RuntimeRoot` separately, so a candidate need not live beside SDL/BGFX resources.

## Development checks

Install the test dependencies once in the Python environment used for this repo:

```powershell
python -m pip install -r requirements-test.txt moderngl
```

Run the former hosted check inventory locally:

```powershell
python harness/local_checks.py
```

This creates a new `results/diagnostics/local-checks-*/` directory containing
`report.json`, the full source identity, per-command logs, native math/FFB data
and the GPU quality report. It runs the Python suite, every standalone native
test, host C31 math vectors, motor and T-junction analyzers, and actual OpenGL
quality fixtures. No ROMs, emulator or physical wheel output are involved.
Missing dependencies, nonzero exits and source changes during the run fail.
Failed evidence stays available. Existing output directories are never reused.

The compiler is selected with `--cxx PATH`, `CXX`, `g++` on PATH, or this PC's
`E:/msys64/mingw64/bin/g++.exe`. Only the compiler subprocess environment gains
its DLL directory; the selected Python interpreter stays fixed. OpenGL 4.3 is
required. `--group python|native|gpu` is useful while iterating, but subset runs
cannot clear a release gate. Linux runs remain supported; they do not establish
Windows launcher coverage. The disabled hosted fallback uses the same runner.

For a native change, build MAME locally using the [developer setup](INSTALL.md#developer-setup-build-from-source)
and keep `patch/vunit-poc-patches.patch` synchronized with the built native tree.
Use the separate targets above for incremental compilation and explicit deployment.
Python/docs-only changes do not need a MAME rebuild.

## Release sequence

1. Commit the intended source and native patch export. Run all local checks on
   that source and keep their output directory. Commit documentation separately
   if needed; changing product/check inputs requires renewed evidence.
2. Assemble a candidate locally with `./build_local.ps1 -Target Release -Version v0.4.1-rc1`
   (example next candidate label, **not** an instruction to publish). Use the explicit candidate options on `make_release.ps1` when packaging another binary.
   Packaging freezes launcher/setup, checks fresh CRT/widescreen defaults,
   verifies the ZIP and emits its file manifest. It does not build MAME.
3. Test the extracted candidate using the complete replay suite, fresh boots,
   GPU/menu/package/upgrade checks and attended checklist in
   [RELEASE-CHECKLIST.md](RELEASE-CHECKLIST.md). Bind evidence to its actual
   executable and the exact ZIP. A different compile is a different candidate.
4. Supply `--checks CHECK_DIRECTORY/report.json` to `release_gate.py` along with
   the existing candidate, regression, fresh-boot and attended evidence. The new
   automated gate requires a complete Windows local report, no skipped unit
   tests, matching source identity, all commands passing and intact evidence
   hashes. Human waivers cannot bypass this gate.
5. Run `promote_release.py` with the same `--checks` report and all other required
   evidence. It defaults to a dry run. After release authorization, add
   `--publish` to upload the **same tested ZIP** through the GitHub Releases API.
   It never recompiles, depends on no Actions artifact, and refuses existing tags.

Keep the ZIP and its `.check.json`, `.defaults.json`, `.manifest.json`, local check
directory and acceptance evidence together. No new release was created by this
migration; v0.4.0 remains the published baseline. Historical cross-platform CI
receipts remain valid evidence for their recorded revisions, not current passes.

GitHub documents [uploading local files with `gh release create`](https://cli.github.com/manual/gh_release_create).
Our promotion tool uses that command after its local gate. Hosted runner usage
is separate [Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions);
this workflow does not schedule an Actions runner for building or uploading.
