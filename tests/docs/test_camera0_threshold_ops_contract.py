from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_intensity_sweep_wrapper_documents_preview_preflight_and_confirmation_gates() -> None:
    script = _read("scripts/intensity_sweep.sh")

    assert "Uso:" in script
    assert "plan|preflight|live" in script
    assert "CAMPAIGN_ID" in script
    assert "--campaign-id" in script
    assert "--index 0" in script
    assert "[PREVIEW]" in script
    assert "[PREFLIGHT]" in script
    assert "OPERADOR_CONFIRMA_LIVE=SI" in script
    assert "no pooling legado" in script.lower()


def test_camera0_threshold_summary_template_includes_acceptance_checklist_and_required_artifacts() -> None:
    summary = _read("data/derived/presentation/camera0_intensity_threshold_summary.md")

    assert "# Resumen de umbral de intensidad - cámara 0" in summary
    assert "## Checklist de aceptación" in summary
    assert "ID de campaña" in summary
    assert "run_intent=threshold" in summary
    assert "camera_index=0" in summary
    assert "data/derived/studies/camera0_intensity_per_pulse.csv" in summary
    assert "data/derived/studies/camera0_intensity_by_duty_wilson.csv" in summary
    assert "data/derived/studies/camera0_threshold_estimates.csv" in summary
    assert "data/derived/studies/camera0_validation_report.csv" in summary
    assert "data/derived/presentation/plots/camera0_duty_detection_ci.png" in summary
    assert "data/derived/presentation/plots/camera0_threshold_bootstrap.png" in summary
