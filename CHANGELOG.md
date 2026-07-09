# Changelog

All notable changes to `miniworlds-robot` are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.1.5] - 2026-07-07

### Added
- New robot ability `can_move` (`robot.can_move() -> bool`) that reports whether
  the next `step()` would succeed (free tile, inside the world). Worlds opt in
  via `robot_abilities`. Lets learners write conditional loops such as
  `while robot.can_move(): robot.step()` without reaching into internals.

### Changed
- Pin `miniworlds>=4.3` dependency so core updates can no longer silently break
  the robot API.
- `task()` now accepts a `position` keyword argument, matching the `load()`
  signature. Examples can override the start position without dropping down to
  `load()`.
- Declare `license = "MIT"` in `pyproject.toml` (PEP 639) alongside the
  classifier.

### Fixed
- `load_world_config_from_url()` now rejects non-http(s) schemes up front,
  preventing `urlopen` from following `file://` or `ftp://` URLs (SSRF hardening).
- Consolidated `Position` type alias to `Tuple[int, int]` across modules; it was
  previously declared as `Tuple[float, float]` in `world.py` but used as integer
  tuples everywhere else.
- `is_solved()` now normalizes positions to `(int, int)` before comparing robot
  and object state. Previously, `_robot_positions()` and `_object_state()` sorted
  raw actor positions, which could be floats from the core and break the
  comparison silently.
- Refactored `_step()` to share the destination/blocked check with the new
  `_can_move()`, eliminating a duplicated `get_destination`/`is_blocked` lookup.

### Removed
- Unused `collectable` class attribute on `RobotObject` / `Leaf`. Leaf removal
  is driven by `isinstance(actor, Leaf)` and never consulted `collectable`.
- Public `create_robot()` factory renamed to `_create_robot()`; it was an
  internal helper used only by `load_robot()` and not part of `__all__`.

### Tests
- Live network tests (`test_world_can_be_loaded_from_published_github_repository`,
  `test_published_github_repository_contains_concept_worlds`,
  `test_load_reads_start_position_from_json_url`) are now marked
  `@pytest.mark.network` and skipped by default in offline CI.
- Added `test_task_accepts_explicit_position` covering the new `task()` argument.
- Added `test_world_config_url_loader_rejects_non_http_scheme` covering the
  scheme validation.
- Added `can_move` tests: blocked by object, blocked by world border, free tile,
  ability required, and a `while`-loop scenario.
- Added `is_solved()` tests: float-position normalization, multi-kind object
  comparison, and missing-object detection.

## [0.1.4] - earlier

- Replace track overlays with clean checkerboard background.
- Add CI workflow to publish to PyPI on version tags.
- Improve normal robot visuals.
- Support URL world loading in Pyodide.
- Support loading robot worlds from URLs.
- Add graphical robot mode.
- Improve robot world behavior.
- Initial import.
