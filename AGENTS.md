# Agent instructions

## Scope and repository map

This repository contains the Python Home Assistant custom integration `ksenia_lares`.
Keep changes focused on the requested fix; preserve existing entity identities,
stored configuration, alarm behavior, and repository conventions.

- `custom_components/ksenia_lares/config_flow.py`: setup and options forms.
- `__init__.py` in that directory: setup, unload, migration and option reload.
- `base.py`: Lares HTTP/XML client; `coordinator.py`: refresh coordination.
- Platform modules: alarm control panel, binary sensors, sensors and switches.
- `manifest.json`: integration version and Python dependencies.
- Root `hacs.json`: HACS metadata and minimum Home Assistant version.
- `.github/workflows/main.yml`: hassfest, HACS validation and pytest matrix jobs.

## Architecture

The integration polls the panel's HTTP web interface (`local_polling`, no push):
XML documents under `http://<host>:<port>/xml/...` with HTTP Basic Auth. The
installer must enable the panel's web interface, which is often disabled by default.

- `LaresBase` (`base.py`) is the only code that talks to the panel. Reads go
  through `get(path)`, which returns a parsed `lxml` tree or `None` on any error
  (errors are logged at debug, not raised). Commands go through `send_command()`
  (`cmd/cmdOk.xml?cmd=...&pin=...`); never log that URL.
- `LaresDataUpdateCoordinator` polls zones and partitions every `scan_interval`
  seconds (options flow, default 10). Its `.data` dict is the single source of
  truth for all entities, which are `CoordinatorEntity` subclasses created from
  the one config entry: a motion `binary_sensor` per zone (on when `ALARM`), an
  enum `sensor` per partition, one `alarm_control_panel`, and a bypass `switch`
  per zone.

### HA alarm states, scenarios and partitions

The options flow maps each HA state (away/home/night/disarmed) to two different
things; keep them distinct:

- Arming and disarming activate a configured **scenario**: its name is resolved to
  an index in `scenario_descriptions()` and passed to `activate_scenario()`.
  A state is only offered when its scenario is configured.
- The displayed state is read from **partitions**: a state applies when all of its
  mapped partitions are armed; otherwise the panel reports `ARMED_CUSTOM_BYPASS`.

Arm/disarm use the code entered in the HA UI for each action. Zone bypass has no
prompt and uses the PIN stored in the options; without it, bypass does nothing.

### Conventions and gotchas

- `get_model()` derives `16IP`/`48IP`/`128IP` from the product name; the suffix is
  part of the zone/partition XML filenames (scenario files have none).
- Entity unique IDs use the position in the XML lists (`lares_zones_{idx}`,
  `lares_partitions_{idx}`, `lares_bypass_{idx}`), so reordering zones on the panel
  shifts entities. Bypass commands send `zoneId = idx + 1` (the panel is 1-indexed);
  everything else uses the 0-based list index.
- Zones/partitions reported as `NOT_USED` are still created, but disabled and
  hidden by default in the entity registry.
- Description lists are cached on `LaresBase`; status lists are fetched on every
  poll. Panel reconfiguration needs an entry reload.
- The device identifier is the panel MAC (via `getmac`), or `host:port` when the
  MAC cannot be resolved.
- `async_migrate_entry` upgrades v1 entries to v2 by adding `port=4202`. Bump
  `ConfigFlow.VERSION` and extend it for any future stored-data change.
- Manual check: copy `custom_components/ksenia_lares/` into a Home Assistant
  `config/custom_components/`, restart and add the integration from the UI.

## Default skill: Ponytail

Use **Ponytail full** by default for every coding, review, dependency and maintenance
task, unless the user explicitly disables it. Before starting, read the installed
`ponytail` skill. If unavailable, retrieve this reviewed upstream source:
[Ponytail SKILL.md](https://github.com/DietrichGebert/ponytail/blob/09c434ab73ca43761c5d8b0c5d341926c2fba710/skills/ponytail/SKILL.md).

Apply its smallest-complete-change approach: inspect affected callers and data,
reuse existing code and platform features, fix the root cause, and verify the result.
Keep error handling, validation and security intact. Do not add frameworks,
abstractions, dependencies or unrelated refactors for a small fix.
A trivial metadata change needs validation, not a new test framework.

If the skill cannot be loaded, explicitly report that limitation and follow the
principles above; do not claim the skill was executed. A missing optional tool
must not stop independently actionable work.

## Targeted community skills

Read only the skill relevant to the task, using an installed copy or the pinned
source below. Follow referenced files when needed. These are community guidance,
not official Home Assistant or HACS requirements.

| Task | Skill |
| --- | --- |
| HACS metadata, manifest and repository layout | [ha-hacs](https://github.com/L3DigitalNet/Claude-Code-Plugins/blob/e3ea15165f8f62c2195a6e3fc42d3794eb6f2cf0/plugins/home-assistant-dev/skills/ha-hacs/SKILL.md) |
| CI or an explicitly requested release/publication | [ha-hacs-publishing](https://github.com/L3DigitalNet/Claude-Code-Plugins/blob/e3ea15165f8f62c2195a6e3fc42d3794eb6f2cf0/plugins/home-assistant-dev/skills/ha-hacs-publishing/SKILL.md) |
| Python integration lifecycle, config/options flow or entities | [home-assistant-integration](https://github.com/denysdovhan/agents/blob/49965622f3b083d1620443e05a37968c7447570f/skills/home-assistant-integration/SKILL.md) |

Review date: 2026-10-18. Do not automatically install a whole plugin bundle or run
remote installer scripts. Revisit pins deliberately when updating these instructions.
Scope takes precedence over broad skill checklists: a targeted fix does not authorize
a whole-repository quality-scale migration or extra workflows.

Known caveats in the reviewed HACS skills: releases are described too broadly as
mandatory, and HACS validation is conflated with hassfest. Official HACS docs allow
default-branch distribution without releases; this repository runs the validators
as separate jobs. Do not copy those claims or scaffold examples uncritically.

Authoritative references:
- [HACS integration requirements](https://www.hacs.xyz/docs/publish/integration/)
- [HACS validation action](https://www.hacs.xyz/docs/publish/action/)
- [Home Assistant manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/)
- [Home Assistant options flow](https://developers.home-assistant.io/docs/config_entries_options_flow_handler/)
- [Home Assistant source](https://github.com/home-assistant/core)

## Branch and PR workflow

1. Read current branch/PR state, changed files and relevant instructions first.
   With a checkout, inspect `git status` and preserve unrelated user changes.
2. For a requested update to an open PR, use its actual head repository and branch.
   For new work after a merge, create a fresh branch from current `main`;
   never keep committing to the merged branch.
3. Read files at the intended ref. For GitHub API updates, use the latest file blob
   SHA and write sequentially; do not overwrite concurrent changes.
4. Inspect both the diff and affected callers/lifecycle, not just the changed line.
   Distinguish regressions introduced by the PR from existing defects.
5. If an external fork rejects a write with 403, do not retry equivalent writes or
   work around access controls. For an authorized fix, create a companion branch/PR
   in this repository and explain why the original PR could not be edited.
6. Open/update a focused PR with problem, changes, compatibility impact and actual
   validation results. Do not merge, tag or publish unless the user requests it.

## Home Assistant compatibility

- Verify changed APIs against official docs and source for the relevant HA versions.
- `OptionsFlow.config_entry` is supplied by HA from 2024.12 onward. Do not assign it.
  Read it only after flow initialization, not inside `__init__`.
  A constructor argument may still be used directly to initialize a client.
- For options-flow changes, check existing defaults, submitted values, persistence
  and the existing reload listener. Avoid introducing duplicate reload mechanisms.
- Match `hacs.json.homeassistant` to the oldest version actually supported by the
  APIs and dependencies. An API introduction date alone is not a full compatibility
  test. Record any lower-bound runtime coverage that is missing.
- Do not alter entity unique IDs, configuration versions or migration behavior
  incidentally. Inspect consumers when changing stored option keys.

## Dependency fixes and validation

- Read the failing job log first. Fix the actual requirement conflict.
- For packages shared with HA, follow current hassfest guidance: use supported
  minimum versions (`>=`) rather than conflicting exact pins. PR #51 established
  `lxml>=6.1.2` and `getmac>=0.9.5`; re-check current requirements before changing them.
- Keep required dependencies declared. Check API compatibility and minimum Python/HA
  support; do not add upper bounds or broad upgrades without evidence.
- Preserve valid JSON, manifest domain, integration version and HACS metadata.
  Bump release versions only as part of requested release work.
- Use existing tests/scripts if present. For non-trivial behavior changes, add focused
  regression coverage using mocked panel responses. See `tests/README.md` for the
  pytest harness and minimum/current HA environments. Run both for compatibility
  changes; never use a real panel in automated tests.
- After pushing, inspect `validate` (hassfest), `HACS Action` and both test jobs for the
  latest PR head SHA. If failing, inspect logs, fix in scope and check the new SHA.
  A previous green run does not validate a newer commit.
- Do not disable checks to obtain green CI. Moving upstream validators can expose
  existing issues; identify them explicitly.
- CI validates packaging/metadata, not physical-panel behavior. Never present a
  contributor's hardware test as your own. Do not send alarm, disarm or bypass
  commands to a real panel without explicit authorization for that action.
- Never log or commit credentials, PINs or command URLs containing PINs.

## Completion

Report the PR link, concrete changes, exact checks and remaining limitations.
Keep user-facing replies concise and in the user's language. State whether work
was only reviewed, committed, validated or merged; do not blur those states.
