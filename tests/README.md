# Tests

The suite uses pytest and `pytest-homeassistant-custom-component` to exercise real
Home Assistant config/options flows and platform lifecycle, mocking the Lares
client at the integration boundary. Command logging tests use the real client
command builder with mocked HTTP responses. No panel or credentials are needed.
Network sockets are blocked by pytest-socket (Unix sockets remain available for
the asyncio event loop). All test credentials and PINs are synthetic.

## Run locally

Use the matching Python and requirements file; do not mix the HA fixture package
from one environment with the other Home Assistant version.

| Target | Python | Home Assistant | Fixture package |
| --- | --- | --- | --- |
| minimum | 3.12 | 2024.12.0 | 0.13.190 |
| current | 3.14 | 2026.10.2 | 0.13.373 |

For example, with Python 3.14 installed:

```sh
python3.14 -m venv .venv-current
.venv-current/bin/python -m pip install -r requirements-test-current.txt
.venv-current/bin/python -m pytest --cov=custom_components.ksenia_lares --cov-branch --cov-report=term-missing --cov-report=xml
```

For the minimum target, use Python 3.12, `.venv-minimum`, and
`requirements-test-minimum.txt`. On Windows, use the environment's `Scripts`
directory instead of `bin`.

The two targets run on each pull request alongside hassfest and HACS validation.
CI publishes separate coverage XML artifacts. Coverage is a baseline, not a
claim of full integration coverage; there is no arbitrary percentage gate.

## What is covered

- User setup, invalid authentication and unexpected setup errors.
- Opening options with existing defaults, without exposing the saved PIN in the
  form; saving explicitly supplied options.
- Keeping the saved PIN when the options form leaves it omitted or blank, and the
  configurable polling interval: default for older entries, range and reload.
- Real setup of all four existing platforms, scheduled polling, cleanup after
  unload, and an options-triggered reload without duplicate registry entries.
- Scenario and zone bypass/unbypass commands, successful and rejected responses:
  the outgoing request contains the synthetic PIN but debug logs do not.
- Output switches: missing or short output metadata keeps bypass switches, stale or
  missing output data is unavailable, slow/malformed output responses do not block
  zone/partition updates, and commands report rejection or a missing PIN.

## Maintaining the suite

Prefer public HA flow, state, service and registry APIs; patch panel I/O, not the
behavior under test. Advance HA time instead of sleeping. Keep sanitized response
fixtures small. Add focused regressions for changed behavior, especially malformed
XML, unavailable panels, rejected commands and reconnects as those paths evolve.

Update the current HA and fixture-package pins together and use their required
Python version. Keep the minimum target aligned with `hacs.json`. Top-level test
dependencies are pinned; transitive ranges can still resolve differently over
time. The explicit async-timeout dependency supports the coordinator's existing
import. These are test dependencies, not changes to the integration manifest.

These tests do not verify physical-panel operation, every supported HA release,
or every allowed runtime dependency version.
