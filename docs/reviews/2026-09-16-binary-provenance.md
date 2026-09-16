# Record executable build provenance, not its enclosing checkout

The recorder populated emulator_source from the Git repository containing the
executable. Frozen candidates live under the collection checkout, so this field
incorrectly named the collection commit as MAME's source. Even an executable in
the MAME checkout can predate its current HEAD. Neither location proves which
source produced the binary.

New recordings leave emulator_source unknown unless an accompanying
vunit.exe.build.json attestation matches the executable's SHA256. That bounded
receipt identifies the native commit/tree, exported patch hash and build-log
hash. The recorder archives it alongside the executable and fingerprints it as
a dependency. The enclosing checkout remains separately labeled
executable_location_source. Replay reports use the same checked attestation;
prepared launch plans also pin its hash.

After a verified native export, attach its receipt with:

```powershell
python harness/binary_provenance.py build/candidates/COMMIT/vunit.exe --export-receipt PATH/TO/native-export.json
```

This validates an existing build attestation against exact binary bytes. It does
not reconstruct the source tree or compile the binary itself. Use the verified
export workflow first; never fabricate provenance from the current checkout.
Missing receipts remain unknown. Mismatched/malformed receipts fail before game
launch, and an existing receipt cannot be silently overwritten.

Sixteen focused tests pass, including recording archival and existing prepared
launch checks. The actual257-patch candidate now has a receipt naming native
1800458b8e3. A real prepare-only replay plan and subsequent live-case freeze
retain that receipt and distinguish it from the collection commit. Neither
operation launches gameplay. Evidence is under
race-transitions-20260916/provenance-{plan,recording,qualified.json}.

Historical case manifests were not rewritten. Their executable hashes and
separate verified export receipts remain the source of truth; their old
emulator_source field must not be treated as a verified MAME revision. Personal
preferences, the Stream Deck binary and the public release remain unchanged.
