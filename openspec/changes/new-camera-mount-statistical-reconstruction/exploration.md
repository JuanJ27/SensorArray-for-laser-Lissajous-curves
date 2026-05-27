## Exploration: new-camera-mount-statistical-reconstruction

### Current State
The current dual workflow couples `tools/webcam_flash_detector.py` and `tools/capture_op598_response.py` via `tools/run_dual_flash_experiment.py`, then feeds offline reconstruction from `data/derived/studies/dual_random_train_runs.csv` into `analysis/reconstruction.py` (`selection_limit=3`, phase offsets `-2..+2`).

Operational defaults assume a stable optical geometry from prior campaigns: camera index `2`, fixed detector defaults (`metric=max`, `threshold-delta=30` in wrappers, dual default `coincidence-window-ms=100`), and baseline calibration done immediately before each run (`warmup`, `calibration`). Existing docs and scripts are tuned to that old mount geometry.

The new camera position changes light distribution, ROI relevance, glare/background behavior, and potentially frame-level detectability thresholds. This can invalidate comparability with prior `random-train_20260522_*` runs used in current reconstruction outputs.

### Affected Areas
- `tools/webcam_flash_detector.py` — detector thresholding and ROI strategy are baseline-sensitive and geometry-sensitive.
- `tools/run_dual_flash_experiment.py` — campaign defaults (index/exposure/threshold/window) and run manifesting for dual runs.
- `tools/run_led_flash_experiment.py` — quick-start orchestration currently assumes legacy detector conditions.
- `tools/run_led_intensity_sweep.py` — detectability thresholds currently expected from old geometry.
- `tools/run_flash_parameter_sweep.py` — exposure/duration sweeps needed for re-baselining after mount change.
- `scripts/flash_experiment.sh` — hardcodes camera index `2` and prior demo settings.
- `scripts/intensity_sweep.sh` — hardcodes old sweep profile and assumptions.
- `scripts/flash_parameter_sweep.sh` — hardcodes old parameter grid and index.
- `analysis/reconstruction.py` — selection/aggregation currently pools runs without explicit campaign partitioning by mount setup.
- `docs/webcam_led_flash_experiment.md` — operational guide currently written for old setup defaults and examples.
- `docs/agent_handoff_webcam_led_flash_experiment.md` — handoff/checklists mention old practical baselines and expected behavior.
- `data/derived/reconstruction/reconstruction_overview.md` — current narrative/claims are tied to old selected runs and should not be treated as mount-agnostic.

### Approaches
1. **Operational-only campaign reset (new run protocol, minimal code touch)** — Keep tooling behavior, but define a strict new campaign procedure: fresh dark-control, fresh sweep, then multiple 2-minute random-train runs with new campaign tagging convention.
   - Pros: Fastest path; low implementation risk; preserves existing scripts/toolchain.
   - Cons: Relies on operator discipline; weaker guardrails against mixing old/new mount runs; reproducibility depends on manual metadata hygiene.
   - Effort: Low

2. **Metadata-first hardening (campaign-aware without algorithm change)** — Add explicit campaign metadata conventions and data-separation rules (docs + run catalog expectations) so old/new mount datasets cannot be silently pooled.
   - Pros: Stronger reproducibility; safer downstream reconstruction validity; improves auditability.
   - Cons: Requires updates across docs/scripts/catalog assumptions; moderate coordination overhead.
   - Effort: Medium

3. **Adaptive detector workflow (re-tune detection controls for new geometry)** — Introduce explicit ROI-first and threshold recalibration playbook (and potentially parameterized script presets) before any statistical run production.
   - Pros: Better signal quality under changed optics; lower false positives/false negatives; cleaner dual coincidence tables.
   - Cons: More operator setup time; risk of overfitting detector settings to one day’s conditions unless documented as campaign config.
   - Effort: Medium

### Recommendation
Use a combined path anchored on **Approach 2 + 3**, executed operationally in two stages:
1) **Dark-control + detector re-baseline stage** (new mount): verify camera index/exposure/FPS stability, measure dark baseline, tune ROI + threshold behavior.
2) **Campaign production stage**: run multiple 2-minute `random-train` dual acquisitions under fixed, versioned settings and explicit campaign labeling.

This gives immediate progress for the new mount while protecting statistical reconstruction validity by preventing silent cross-campaign pooling with legacy geometry data.

### Risks
- **Dataset contamination risk**: old and new mount runs can be accidentally pooled in derived tables/reconstruction.
- **Threshold drift risk**: old `threshold-delta` and metric choices may under/over-detect after geometry change.
- **Coverage risk**: 2-minute runs can degrade to partial coverage if webcam settings (exposure/FPS) drift.
- **Comparability risk**: old published detectability claims (duty/duration thresholds, offsets) may not transfer to new mount.
- **Operational fragility**: script defaults hardcode camera index `2`; mount/system changes may shift device index.

### Ready for Proposal
Yes — proceed to `sdd-propose` with scope centered on campaign protocol, metadata separation, and script/doc alignment for the new camera mount before generating new reconstruction claims.
