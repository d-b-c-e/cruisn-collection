# Public documentation audit — 2026-09-08

Reviewed the live launcher row builders, graphics/force option resolution, cheat
import/preparation, shifter/cabinet setup, telemetry environment handling, local
checks, packaging and promotion against the current guides. The top-level repo
map was compared with tracked source files. Historical checkpoints stay dated.

| Gap | Correction |
|---|---|
| README mixed released and overnight work; linked a completed work order as current | Current roadmap/index and a v0.4.0/source capability table; separate guest-distance menus from the CLI host prototype |
| Setup claimed tag pushes build/publish | Local builds/checks and exact-ZIP promotion; disabled hosted workflows |
| Release-morning guide still selected rejected rc2 and said no release existed | Current reusable attended protocol; rc1/rc2 clearly historical and v0.4.0 preserved |
| Flat menu paths, removed per-game strength/Peak Limit, wrong STANDARD default | Actual Controls/Support/Force Feedback paths, shared strength and CRISP default |
| Exotica both “always AUTO” and “manual works”; obsolete steering-mirror instructions | Cabinet selection and virtual paddle shifter described separately from force polarity; no all-gear physical acceptance claim |
| New World/Off Road/Exotica options missing from setup | Applicable games, defaults, prerequisites and measured limits documented |
| All-game rev signals existed but player telemetry setup was absent | Estimated RPM explanation and matching Forza-compatible UDP configuration |
| “No game assets” contradicted bundled menu media | State exactly what is packaged; identify media provenance and original-code licensing decisions before public access |
| Agent guides described an early POC and tag publication | Current module map and local workflow; CLAUDE.md delegates to shared AGENTS.md instead of duplicating stale instructions |
| Old design/handoff pages looked like live instructions | Archive notices and current-guide links; research findings/failed evidence preserved |

The final bounded link audit checked all 77 top-level/`docs/` Markdown
documents, including CLAUDE.md and this review, with no missing relative link
targets or unbalanced code fences. The normal-launch fix was tested separately: 187 local tests,
native helpers, 24 GPU checks, with failure/evidence archives retained.

Public access is still preparation. No repository visibility change, new release,
licence selection, full Git-history audit or asset-rights determination was made.
See [the outstanding public checklist](../PUBLIC-READINESS.md).
