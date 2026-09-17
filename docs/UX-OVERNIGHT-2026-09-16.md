# Cruis'n Collection: overnight UX candidate

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

## Placement inventory

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

## Explicit gaps and game limitations

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
