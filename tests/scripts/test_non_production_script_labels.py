from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read_script(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_flash_experiment_script_is_explicitly_non_production_demo() -> None:
    script = _read_script("scripts/flash_experiment.sh")

    assert "[NON-PRODUCTION]" in script
    assert "run_intent=demo" in script
    assert "run_dual_flash_experiment.py" not in script


def test_intensity_sweep_script_is_explicitly_non_production_tuning() -> None:
    script = _read_script("scripts/intensity_sweep.sh")

    assert "[NON-PRODUCTION]" in script
    assert "run_intent=tuning" in script
    assert "run_dual_flash_experiment.py" not in script
