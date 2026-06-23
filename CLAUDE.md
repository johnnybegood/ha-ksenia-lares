# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Home Assistant **custom integration** (HACS-distributed) for Ksenia Lares alarm panels
(16IP / 48IP / 128IP, also sold rebranded by BTicino). All code lives under
[custom_components/ksenia_lares/](custom_components/ksenia_lares/). There is no application
to run standalone — it loads inside a Home Assistant instance.

## Development & validation

- **No build, no test suite, no linter config in-repo.** CI on every PR
  ([.github/workflows/main.yml](.github/workflows/main.yml)) runs only
  `home-assistant/actions/hassfest` (validates `manifest.json` / integration structure) and
  the HACS action (validates HACS packaging). Match those expectations when changing
  `manifest.json`, `hacs.json`, or `strings.json`/`translations/`.
- **Manual testing** = copy `custom_components/ksenia_lares/` into a real HA instance's
  `config/custom_components/`, restart HA, and add the integration via the UI. The panel's
  web interface must be enabled by the installer (often disabled by default).
- **Releasing**: bump `version` in [manifest.json](custom_components/ksenia_lares/manifest.json)
  (HACS reads the GitHub release tag). Runtime deps are pinned there (`lxml`, `getmac`).

## Repository & contribution workflow

This checkout is a **fork**. The remotes are:

- `origin` → `pierfani/ha-ksenia-lares` (personal fork; `main` tracks `origin/main`).
- `upstream` → `johnnybegood/ha-ksenia-lares` (the original repo, where releases live).

Contributions go upstream via **fork pull requests**:

1. Branch off `main` (don't commit fixes directly on `main`).
2. Commit, then `git push -u origin <branch>` to the fork.
3. Open the PR against `upstream/main`. **`gh` CLI is not installed here** — open PRs via
   the GitHub "compare across forks" URL:
   `https://github.com/johnnybegood/ha-ksenia-lares/compare/main...pierfani:ha-ksenia-lares:<branch>?expand=1`
4. Link related issues in the PR body (`Fixes #NN` / `Closes #NN`).

Consequences to keep in mind:

- A fix lives only on its feature branch / PR until merged upstream — local `main` (and
  `origin/main`) will still show the **pre-fix** code. That's expected, not a lost change.
- After a PR is merged upstream, resync: `git fetch upstream && git merge upstream/main`
  (or `git pull upstream main`), then `git push origin main` to realign the fork.
- `CLAUDE.md` is a local tooling artifact: keep it out of upstream PRs (commit it only on the
  fork's `main`).

## Architecture

The integration talks to the panel over its **HTTP web interface**, fetching static-ish XML
documents under `http://<host>:<port>/xml/...` with HTTP Basic Auth. `local_polling`, no push.

### Layers (read in this order)

1. **[base.py](custom_components/ksenia_lares/base.py) — `LaresBase`**: the only thing that
   touches the panel. Every read is `get(path)` → returns a parsed `lxml` element tree (or
   `None` on any error — errors are swallowed and logged at debug). Writes go through
   `send_command()` which hits `cmd/cmdOk.xml?cmd=...&pin=<code>&...`.
2. **[coordinator.py](custom_components/ksenia_lares/coordinator.py) — `LaresDataUpdateCoordinator`**:
   a HA `DataUpdateCoordinator` polling `zones()` + `partitions()` every **10s**. Its
   `.data` dict (`{DATA_ZONES, DATA_PARTITIONS}`) is the single source of truth all entities read.
3. **Platform entities** — all are `CoordinatorEntity` subclasses, all set up from the one
   config entry:
   - [binary_sensor.py](custom_components/ksenia_lares/binary_sensor.py): one per **zone**,
     `device_class=motion`, `is_on` when zone status is `ALARM`.
   - [sensor.py](custom_components/ksenia_lares/sensor.py): one per **partition**, an ENUM
     sensor exposing the raw partition status.
   - [alarm_control_panel.py](custom_components/ksenia_lares/alarm_control_panel.py): a single
     panel entity (see mapping below).
   - [switch.py](custom_components/ksenia_lares/switch.py): one per **zone**, toggles bypass.
4. **[config_flow.py](custom_components/ksenia_lares/config_flow.py)**: initial setup (host /
   port `4202` / username / password) + an **options flow** that builds the state→scenario
   mapping and stores the bypass PIN.

### The central concept: HA states ↔ Ksenia scenarios + partitions

Ksenia has richer scenarios than HA's fixed `away`/`home`/`night`/`disarmed`. The options flow
([config_flow.py](custom_components/ksenia_lares/config_flow.py)) maps each HA state to **two
different things**, and getting this distinction wrong is the most common source of bugs:

- **Arming uses a *scenario*** (`CONF_SCENARIO_*`): `async_alarm_arm_*` looks up the configured
  scenario *name*, resolves it to an index against `scenario_descriptions()`, and calls
  `activate_scenario(idx, code)`.
- **Reading state uses *partitions*** (`CONF_PARTITION_*`): the panel's `state` property checks
  whether *all* partitions mapped to a given HA state are armed. If armed partitions don't match
  any mapping, it falls back to `ARMED_CUSTOM_BYPASS`.

So a feature (e.g. `ARM_HOME`) is only advertised when its scenario is configured, but the
displayed state depends on the partition mapping — the two must be configured consistently.

### Two different "codes"

- **Arm/disarm**: the code is entered live in the HA UI per action and passed straight to
  `activate_scenario(scenario, code)` as the panel PIN.
- **Zone bypass**: there is no per-action prompt; it uses the **PIN stored in options**
  (`CONF_PIN`). If that option is unset, bypass silently no-ops with an error log.

## Conventions & gotchas

- **Model suffix drives XML paths.** `get_model()` inspects the product name and returns
  `"16IP"`/`"48IP"`/`"128IP"`; that suffix is interpolated into description/status filenames
  (e.g. `zonesStatus48IP.xml`). Scenario files are not model-suffixed.
- **Entities are keyed by positional index**, not panel ID — `lares_zones_{idx}`,
  `lares_partitions_{idx}`, `lares_bypass_{idx}`. Indices come from list position in the XML, so
  reordering on the panel side would shift entities.
- **Off-by-one in bypass**: `bypass_zone()` sends `zoneId = idx + 1` (panel zones are 1-indexed)
  while everything else (sensors, status lookups) uses the 0-based list index. Keep both in mind.
- **Unused entities are hidden, not omitted**: zones/partitions reported as `NOT_USED` or
  without a description are still created but default to disabled+invisible in the registry.
- **Description lists are cached** on `LaresBase` (`_zone_descriptions`, etc.); status lists are
  always re-fetched. A panel reconfiguration won't be picked up without reloading the entry.
- **Device unique ID** = MAC (via `getmac`), falling back to `host:port` when the MAC can't be
  resolved.
- **Config entry migration**: `async_migrate_entry` (v1→v2) backfills `port=4202`. Bump
  `ConfigFlow.VERSION` and extend that function for any future schema change.
