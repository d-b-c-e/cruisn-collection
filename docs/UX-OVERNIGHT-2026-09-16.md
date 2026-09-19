# Cruis'n Collection: overnight UX candidate

## Current deployment — September19

The personal Stream Deck source launcher now includes strict device selection,
endpoint/deadzone/inversion calibration, explicit FFB device selection, and the
latched Stop FFB implementation. Native707 (`f1f908e6`) is deployed from the
accepted renderer lineage; the extended-rendering native4df remains isolated.
All43 owner settings, force profiles and wrapper were preserved. Publicv0.5.0
is unchanged. Exact source/package/deployment identities appear at the end.

The bounded frozen4K live check passed warning/cancel, mouse navigation, modal
F6 cancellation, F8 Off with strength retained, and focus-loss recovery. No
devices were returned by either provider, so actual axis preview/calibration
and physical force remain unaccepted. The empty axis picker exposed a misleading
capability label; its correction is deployed through master753b2de and included
in the final162140 development package. No native change was needed.

**Historical record below:** the original September16 inventory and gap table
are retained to explain the staged rollout. Their pending calibration/device
picker/native-stop claims were superseded by the September19 deployment; they
are not the current task list. Later sections preserve exact stage receipts.

Guidance: UX-1 / UX-01-S, revised 2026-09-16, toolkit commit
`a84bebab5ec2abdcd5140b9c63c139ccff86a7d3`. All five CONSUMER-UX,
SETTINGS-VIEWS, CONTROLS-CAMERAS, SETUP and UX-CHECKLIST documents were read.
Work is on `codex/ux-simple-advanced` in `E:/Source/cruisn-collection-ux-review`.
The personal source launcher, native 87d installation and public v0.5.0 are not
updated. Native rendering work remains on master 839dc7c / native 4df727db105;
the latter's timing-only qualification is held for a coordinated rig slot.

## Implemented frontend changes

- Simple is the fresh/legacy default; explicit view/page preferences persist.
  Switching views writes only presentation keys. A first-save backup retains
  the previous configuration; atomic replacement preserves the file and active
  selection on write failure. Hidden tuning stays effective and is discoverable.
- Six stable page links: Setup, Controls, FFB, Cameras, Telemetry, Help. Keyboard
  Tab changes page; pointer selection uses the same layout. F6 opens/closes the
  launcher panel; Esc closes, and Back rows retain parent navigation.
- Individual axis and button rows start the existing binding capture directly.
  Both views expose ordinary bindings, transmission selection and native camera
  keys. Capture has timeout, Cancel and explicit Save bindings. Delete clears
  only the focused binding. Atomic saves retain other roles and unknown settings.
- Display, experiments, detailed force tuning and diagnostics move to Advanced.
  The old native game menus are retained. No renderer, force gate, calibration
  mathematics or game memory changes are included in this frontend commit.

## Initial September16 placement inventory (historical)

The same values and launch path serve both views. There is no Simple tune.

| Setting/action (saved key) | Page | Placement | Default/unit and purpose |
|---|---|---|---|
| View/page (`settings_view`, `settings_page`) | Fixed header | Both | Simple / Setup; presentation only |
| Readiness / guided setup | Setup | Simple | Reports assignments, not connected or physically verified input |
| Steering, Throttle, Brake (`wheelmap.steer/gas/brake`) | Controls | Simple | Existing mapping retained; missing is Not bound |
| Coin / Start (`coin`, `start`) | Controls / Buttons | Simple on demand | Existing stock key routes retained |
| View1/2/3 (`view1/view2/view3`) | Cameras and Controls / Buttons | Simple on demand | Both entrances edit one binding store |
| Radio (`radio`) | Controls / Buttons | Simple on demand | Native game action |
| Gear1/2/3/4 (`gear1..gear4`) | Controls / Buttons | Simple on demand | Shown for H-pattern; hidden paddle assignments retained |
| Shift up/down (`shiftup/shiftdn`) | Controls / Buttons | Simple on demand | Shown for sequential; H-pattern assignments retained |
| Volume up/down (`volup/voldn`) | Controls / Buttons | Simple on demand | Native game action |
| Test menu / Service credit (`test/service`) | Controls / Buttons | Simple on demand | Operator actions; do not invent Pause/Reset car routes |
| Transmission (`transmission`) | Controls | Simple | H-pattern; legacy paddle-only configuration inferred as before |
| Game ADC calibration | Controls | Simple information | F2 game service menu; frontend calibration remains a gap below |
| Strength (`ffb`) | FFB | Simple |50%;0 currently disables output; unchanged launch semantics |
| FFB device | FFB | Simple information | Saved steering name; actual strict picker is still a gap |
| Spring (`ffb_spring`) | FFB | Advanced |0%; Exotica excluded as before |
| Direction (`ffb_invert`) | FFB | Advanced | Normal; owner value retained |
| Feel (`ffb_profile`) | FFB | Advanced |`cruisn-vunit@2`; unchanged tuning |
| Impact cues (`ffb_impact_<rom>`) | FFB / Impact cues | Advanced | Off; exact ROM revision handling retained |
| CRT (`crt`) | Display | Advanced | On; F9 still works in game |
| Widescreen (`margin`) | Display | Advanced | Full widescreen; owner custom margin retained |
| Internal resolution (`scale`) | Display | Advanced |4x; no rendering initialization changes |
| Crack Fill (`crackfill`) | Experiments / Shared | Advanced | On inherited default; no option removed |
| Seam alignment (`seam_alignment_<game>`) | Experiments | Advanced | Off; V-Unit games |
| Widescreen terrain (`terrain_visibility_crusnwld`) | Experiments | Advanced | Off; World |
| World distance (`world_distance_crusnwld`) | Experiments | Advanced | Off;2x/3x candidates remain optional |
| World lookahead (`world_lookahead_crusnwld`) | Experiments | Advanced |+8, inactive without distance |
| Older distant scenery (`scenery_distance_crusnwld`) | Experiments | Advanced | Off; mutually exclusive distance path retained |
| USA detail / far limit (`detail_distance_crusnusa`, `far_distance_crusnusa`) | Experiments | Advanced | Off; no new promotion |
| Off-Road distance (`offroad_distance_offroadc`) | Experiments | Advanced | Off;2x/3x options retained |
| Exotica widescreen (`wide_visibility_crusnexo`) | Experiments | Advanced | Off; distinct from host-distance prototype |
| Exotica menu feedback (`menu_feedback_crusnexo`) | Experiments | Advanced | Off; owner preference retained |
| Steering sensitivity/curve (`steersens_<rom>`, `steercurve_<rom>`) | Game card | Advanced | Existing game defaults; hidden custom values summarized |
| World revision (`world_rom`) | Game card | Advanced |2.4; existing choice retained |
| Play / volume / free play / cheats | Game card | Simple | Existing NVRAM and exact-revision cheat semantics |
| Forza destination (`telemetry.forza`) | Telemetry | Simple information | Actual saved destination; no false receiver-connected status |
| Diagnostic UDP (`telemetry.udp`) | Telemetry | Advanced information | Actual saved destination |
| Recording | Telemetry | Information | Agent-prepared recording remains a separate bounded launch |
| Support bundle / updates | Help | Simple | Existing actions; support hint discloses its10-second game launch |
| Force diagnostics (`ffb_diag`) | Help | Advanced | Off; active diagnostics summarized in Simple |

Unlisted manual INI/environment overrides are retained, not surfaced as new
controls or silently reset. The retired `marginfill` behavior is unchanged.

## Checks and acceptance boundaries

Six new presentation/persistence/binding tests pass. Existing 22 graphics-option
and 11 launcher/release contracts pass with the deliberate Advanced placement
expectations updated. These use disposable settings and mocked launches; no
game or physical force was exercised. Python compilation and diff checks pass.

`harness/render_settings_fixture.py` runs the actual settings draw method using
a CPU image backend. Ten 720p/4K images pass extent/row-overlap checks; 720p Controls
and Advanced root were viewed. Evidence: local
`results/diagnostics/ux-20260916/layout-v2`. This is layout evidence, not GL,
packaged mouse/keyboard or physical acceptance. Native GPU/game testing is held.
The isolated PyInstaller build passes fresh and legacy `--config-report` checks.
Executable SHA256 is `e84adba72078b6f1ed8f8cc50cf389e205c8d906492b74a279b5328b40d85dee`.
Full source/build/report identities are in local
`results/diagnostics/ux-20260916/frontend-build-v2/qualified.json`.
The first build attempt failed before compilation because the ignored spec is
not checked out in a worktree; the corrected attempt explicitly reads that
build recipe and substitutes the isolated source path. Original failure retained.

Current layout evidence is `layout-v3` (updated Esc footer); ten images still
pass. Examples: [720p Controls](../results/diagnostics/ux-20260916/layout-v3/1280-simple-controls.png),
[4K Setup](../results/diagnostics/ux-20260916/layout-v3/3840-simple-setup.png).
These large local fixtures are not in the public source tree. The shared HTML
reference/README published at toolkit 95cbd89 was reviewed for hierarchy,
short Simple setup, cancellation and common labels; it is not runtime evidence.

## Initial September16 gaps and game limitations (historical)

| Rule | State | Actual limitation / follow-up |
|---|---|---|
| UX-01-S | Partial | View migration/placement implemented; packaged interaction and custom-summary detail follow-ups remain |
| UX-01 | Partial | Launcher F6/core navigation implemented; active game is a separate native process with Esc pause menu. Cross-process shared settings is not implemented, not an inherent ROM restriction |
| UX-04 | Gap | Existing capture detects axis/direction; it does not yet provide endpoint/deadzone/inversion calibration with live final-input bars. F2 operator calibration is an explicit interim route |
| UX-04-H | Not applicable to verified routes | These ROM bindings expose steering, throttle and brake; no verified handbrake game action. No physics action invented |
| UX-05/D | Gap | Existing force selection uses the saved steering name. Dedicated saved Off/On now implemented below. Stable-identity dropdown, explicit override and latched in-game F8 stop remain separate native work |
| UX-05/06 | Owner exception | World menu/race-end force passthrough remains by the owner's explicit instruction to undo menu gating and leave its normalization issue open |
| UX-06/K | Partial / unavailable mounts | Native View1/2/3 can be rebound. No verified host-owned Bonnet/Bumper pose seam exists; no fake pose sliders or numpad actions are offered |
| UX-07 | Partial | Saved Off/On and atomic connection editing implemented below; receiver/live-dialog acceptance remains separate |
| UX-08 | Partial | View/binding saves atomic and failure-visible; older tuning save paths still need the same recovery treatment |
| UX-09/10/11 | Not tested | No installer/update/uninstall or attended first-drive acceptance was performed |

Do not call the overall UX rollout or rendering parity complete from these
fixture results. Next continue the generic configuration gaps without changing
the personal installation or claiming hardware acceptance.


## Telemetry follow-up

The first view split is commit `dd4e7ff`. The next scoped change adds a saved
Telemetry Off/On control in Simple. First enable uses the local Forza/SimHub
preset only when no destination is saved; toggling Off retains custom Forza and
JSON destinations. Advanced Connection settings uses one modal draft with Apply
connection/Cancel and validates both addresses before atomic persistence.

The native sender supports numeric IPv4, one JSON destination and up to four
Forza destinations. The UI matches those limits; unsupported hostnames/IPv6 and
invalid ports are rejected rather than passed to the native parser. Existing
explicit diagnostic environment overrides still win. A malformed saved target
reports an error at launch; the user can correct it in Connection settings.
The launcher dashboard-reset sender honors saved Off and reconfigures only after
an explicit telemetry change, never because of a view/page switch.

Five new no-socket tests pass, covering Off/custom settings, atomic failure,
native address bounds and receiver rows. Four process-boundary test methods
pass, including both telemetry states on all five ROM revisions; Popen is
intercepted before any emulator starts. The existing 11 release/configuration
checks pass. No receiver, modal UI interaction or frozen successor build is
claimed from these checks. The earlier frozen executable remains the view-only
checkpoint until the final frontend rebuild.


## Persistent force switch

The FFB page now offers Force feedback Off/On in both views, separately from
Strength. Off retains strength, spring, direction, profile, impact selections and
steering assignment. A missing switch migrates legacy strength zero to Off;
fresh installs retain the existing On default. A saved Off overrides an inherited
force-enable environment variable, removes force-test injection, and reaches the
common launcher for every ROM. An explicit diagnostic MIDV_FFB=0 remains Off.
The change does not alter any game tune, Exotica output trim or World's menu
force passthrough. This is a next-launch preference, not an in-game emergency stop.

Two new preference tests and five process-boundary test methods pass, including
all five ROM profiles, retained 65% strength, the existing Exotica 52% output trim,
legacy zero, diagnostic Off and no World gate. No physical output was enabled.
Fourteen CPU fixtures in `layout-v4` pass bounds and row-collision checks at 720p
and 4K, including both telemetry views. These are layout tests, not GPU or mouse
interaction acceptance.


## Final isolated frontend build

Frontend commit `3229661` is packaged separately in local
`results/diagnostics/ux-20260916/frontend-build-v3/dist/CruisnCollection`.
Executable SHA256:
`33b1144542b827e3603cc5cb8f17bd598cf39cc94be738f8c82a4deaf845791b`.
Its `qualified.json` attests source hashes and the build log. The reusable
`harness/qualify_frontend_config.py` runs only `--config-report` against isolated
fresh, legacy and explicit saved-Off fixtures. All three pass; configuration bytes
remain unchanged. Fresh defaults include Simple/Setup, CRT On and 4x. Legacy
zero remains force Off; explicit Off retains 65% strength and a custom profile.
Telemetry destinations and saved Off survive. No synthetic rig is placed in the
candidate distribution; fixtures live separately under `config-smoke`.

The candidate is reviewable, not deployed. Source, native emulator, Stream Deck
installation and public release remain unchanged outside the isolated worktree.
This does not qualify physical force, modal input interaction, active-game F8,
rendering parity or a release package.


## Native seam assessment: stop latch and device identity

Read-only audit against native `4df727db105` identifies concrete follow-ups:

- `midvunit_v.cpp::mvffb::select_device` accepts case-insensitive name substrings
  or VID:PID. A named match that lacks haptics fails closed; an unmatched explicit
  name also fails closed. With no explicit name, it still falls back to the first
  suitable wheel/device. Duplicate names or identical VID:PID are ambiguous.
  A frontend dropdown alone cannot prove stable physical association. The native
  selector needs an identity contract, uniqueness check and no fallback for a
  missing saved device; the binding store needs the same identity.
- `midv_ffb_cancel()` zeros the current request and asks the worker to reset
  shaping/impact history. It is not latched: a subsequent game write can resume
  force. Mapping F8 to this function would therefore be an incomplete stop.
- The worker owns constant force, optional rumble and persistent condition effects.
  A true stop must gate every output, clear pending history, stop all owned effects
  on the worker thread, and remain off despite later game writes, menu transitions
  and focus changes. It must have an explicit re-enable path. The owner's World
  menu pass-through is independent of this user-controlled stop.
- The launcher already unbinds MAME's F8/F9 frameskip controls. The settings wizard
  reserves F8, but no native F8 latch exists. Active gameplay and the launcher
  are separate processes; the new saved switch applies at the next launch only.
- An existing device-free native worker sink records requested output without
  loading SDL haptics. Extend that seam to test stop during nonzero constant,
  impact and condition requests, continued source writes and explicit resume;
  then qualify native key delivery and finally attended hardware behavior.

No native code, package or FFB behavior was changed for this audit. This is an
implementation boundary, not acceptance inferred from frontend tests.

## Authorized deployment stage, September 19

The owner authorized local consumer UX deployment through the coordinating task,
superseding this document's earlier no-deploy scope. Public release and unattended
torque are not authorized by that request. The five guidance documents and HTML
reference at toolkit e1f0e3f were reread. Native gaps above remain required work;
frontend rollout alone is not overall UX completion.

Ordinary launcher tuning saves now use the existing atomic section writer and a
`.before-settings.bak` backup. A failed save restores saved values, reports an
error in the launcher and refuses a launch that could otherwise use unsaved
settings. Seven focused settings tests pass, including injected replacement
failure, retained original bytes, backup, unknown keys, independent bindings and
custom telemetry. This closes the direct-write gap in UX-08; live interaction
and broader installer lifecycle remain separate.

Stream Deck's existing Launch-Cruisn.bat launches the source checkout at
`E:/Source/cruisn-collection/harness/collection.py`. A scoped source merge is
therefore a local frontend deployment. It must retain owner rig data and the
personal emulator87d. That emulator's recorded source is native4ac6a84b51b4,
separate from the unqualified4df renderer profiling candidate. Do not deploy the
latest native build using the generic Personal target as part of this frontend
stage. The staged frozen frontend, exact rollout/backup paths and retained
configuration hashes will be recorded after build and installation.

### Frontend stage deployed

Source79a192b is deployed through mergeeb78f4f to the verified Stream Deck source
target. The installed profile's Keypad7,2 opens Launch-Cruisn.bat, which starts
`python harness/collection.py` in `E:/Source/cruisn-collection`. No button or wrapper
was changed. This is a source-checkout rollout, not a player-installer acceptance.

The launcher/game was closed. Backup is
`E:/Source/cruisn-collection/results/diagnostics/ux-20260919-deployment/backup`.
The22 owner configuration files are byte-exact after deployment and config-report
execution, as are personal emulator87d and the wrapper. Seven installed runtime
source blobs match the candidate. `before.json` and `verified.json` retain paths,
hashes and source identity. An initial backup-script separator lookup error stopped
before deployment; its script/failure record remain beside corrected preparation.
The source merge required only an AGENTS documentation conflict resolution.

The frozen frontend is
`E:/Source/cruisn-collection-ux-review/results/diagnostics/ux-20260919/frontend/dist/CruisnCollection/CruisnCollection.exe`,
SHA256 `0ed809c7adf0a65950c20c695c9ef132df5a24ab3f883236ad70bd695a252993`.
The adjacent frontend-only development ZIP `CruisnCollection-frontend-79a192b.zip`
has SHA256 `e8264bd579803ad7af0b10007064c5baff165d80ee9037ea6b84a2d505163c49`.
It requires an existing runtime/assets and is not a public player package.
`qualified.json` retains all payload hashes and build/source/config receipts.
Fresh, legacy and saved-Off frozen fixtures pass. Five merged-source launch-boundary
tests pass with process creation intercepted. No live menu, physical input/force,
installer/uninstaller or broad rendering acceptance is claimed.

Native F8 stop, strict identity and full calibration are the next separate stage,
starting in `E:/Source/mame-ux` from accepted native4ac6a84b51b4. The primary native
parity tree and its frozen profiling candidate are untouched. World menu/race-end
passthrough remains an owner exception. The overall UX reconciliation is incomplete.

## Native stop follow-up in progress

The frontend79a192b stage was deployed separately through mastereb78f4f; consult
the master copy of this document for its exact backup/package verification.
This worktree now stages a successor, not yet deployed:

- F8/Stop FFB in the launcher saves Off without changing Strength or tuning.
  Close and Stop FFB remain visible on every settings page.
- A durable `ffb-user-stopped` marker from the native process overrides saved On
  on restart. Only an explicit On clears it, after the settings write succeeds.
- The common launch path binds the marker to the owner's rig. Recording/replay
  preparation removes an inherited owner path and binds a private run marker;
  an unattended experiment cannot change the owner's force preference.
- Native candidate6dde90ff16a in `E:/Source/mame-ux` is based on accepted4ac6a84b51b4,
  plus only the device-free force-worker observer and the new stop implementation.
  It adds a process latch, worker-owned effect cancellation, both renderer F8
  routes, an Esc Stop FFB action, persistence/failure indication and an explicit
  device-free scheduled-stop test seam. It is not built or runtime-qualified yet.

Three force-preference tests, five launch-boundary methods, eleven session tests
and seven settings tests pass without game/device execution. Fourteen CPU layout
fixtures at720p/4K pass bounds/overlap checks; the720p FFB view was inspected.
Evidence is under local `results/diagnostics/ux-20260919/stop-layout`.
These establish frontend policy/layout only. Native compile, observer stop
qualification, live key/menu delivery and attended hardware checks remain open.
No stable-identity picker or full calibration completion is claimed.

## Reviewed native and controls stage deployed, September 19

The final source6c4407e is merged into the actual Stream Deck source checkout
through master1e6b4ec. The closed-target deployment replaces only personal
`mame-src/vunit.exe` and adds its exact build/capability receipts. Native707 is
based on the accepted4ac renderer; the separate rendering investigation's
native4df source checkout and frozen candidate remain untouched.

The complete development package is
`CruisnCollection-dev-20260919-160053.zip`, SHA256
`f6bf2ef6a4bd2f74473ea7d871a4e7b1c6514a3b74bf28c7c527bcdb69d95653`.
Frozen launcher SHA256 is
`217924616b75b9727128aa1939ace58b5b2e111cd647ca3404984aa366c104c4`;
installed native SHA256 is
`f1f908e66784b657d892e651850693c99e606ffcf093397f9a994975f1c51c01`.
Package validation binds142 native patches, source tree and capability receipt.
Fresh/legacy/saved-Off frozen configuration checks pass without fixture changes;
29 setup,7 common-launch and7 settings tests pass on the integrated source.
The earlier5810 development ZIP is retained unchanged.

Backup and deployment receipts are in
`results/diagnostics/ux-20260919-deployment-v2` in the personal checkout. All43
owner settings files, wrapper, force profiles and runtime dependencies retain
exact bytes. Changed launcher/native helper source has matching Git content;
Windows CRLF checkout differences are recorded with both physical hashes.
The existing newer rendering analyzer is explicitly retained against the
pre-deployment master blob. Two pre-copy validation failures remain: raw LF/CRLF
comparison, then the intentional analyzer divergence. Neither copied a binary;
the corrected scoped verifier passes. Three merge conflicts were documentation
only; both histories and the append-only results were preserved.

Stop FFB remains latched until explicit On; strict axis identity/calibration
and output selection are now carried through the common launch path. Legacy
bindings/strength/tunes remain saved. Legacy owners must confirm their output
device once; unresolved saved-On launches offer Configure, Continue without FFB,
or Cancel. The force-free choice is per launch and cannot be overridden by a
device appearing later. A resolved device has no additional per-race prompt.
World's requested force pass-through is unchanged.

At this stage live checks were still queued. The subsequent bounded live check
and wording successor below supersede that status; physical wheel/force behavior
remains unaccepted. This is local deployment, not public release publication or
extended-rendering acceptance.

## Final wording package and bounded live check, September19

The frozen6c4407e frontend ran at3840x2160 with literalMIDV_FFB0 and isolated
settings. Warning/cancel, pointer navigation, F6 modal cancellation, F8 Off with
50% strength retained, and focus-loss cancellation/return passed. No game ran.
Both providers returned no devices; actual input preview/calibration and physical
forces remain unqualified. Live screenshots were inline Computer Use images,
not saved file captures. The misleading empty-picker readiness label is now
Controls support: Available. FFB's independently resolved device status remains.

Final sourceb8d2c4926aa5e3fa89c0313796a9e2f9fe666b83 is deployed by master753b2de.
Package `CruisnCollection-dev-20260919-162140.zip` SHA256:
`adbd5854869b5fd36da3347ca79e34082681c41c05457fcd724d5d0ca441f1b9`.
Frozen launcher SHA256:
`10058cc02de6b2e78a95511a582a1a01f43754e6c381b1c7930ef296df6aae21`.
Package/default checks and frozen fresh/legacy/saved-Off checks pass. The29
focused setup tests and32 software-rendered720p/4K layouts pass; these layouts
are placement evidence, not live game captures. Earlier packages are retained.

Read-only `verified-wording.json` under the deployment evidence directory passes
all26 source blobs,43 owner settings, the Stream Deck wrapper and reviewed707
runtime/receipts/profiles. No native binary was copied again. The separate4df
rendering source is unchanged. Desktop testing is paused after the user's Escape
in another coordinated test; the queued rendering replay awaits resumption and
a separate rig grant. Nothing is publicly published.
