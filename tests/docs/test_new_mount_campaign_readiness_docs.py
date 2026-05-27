from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read_doc(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_webcam_guide_documents_campaign_gate_and_acceptance_rules() -> None:
    doc = _read_doc("docs/webcam_led_flash_experiment.md")

    assert "Protocolo de campaña de producción (new-camera-mount)" in doc
    assert "5 minutos" in doc
    assert "10 corridas independientes" in doc
    assert "120 s" in doc
    assert "1.8–2.2 s" in doc
    assert "Comandos de readiness (sin medición real)" in doc


def test_handoff_checklist_includes_operational_governance_for_phase4_ready() -> None:
    doc = _read_doc("docs/agent_handoff_webcam_led_flash_experiment.md")

    assert "Gobernanza de campaña (new-camera-mount)" in doc
    assert "run_intent=demo" in doc
    assert "run_intent=tuning" in doc
    assert "freshness <= 5 minutos" in doc
    assert "run_index" in doc
    assert "scripts/new_mount_campaign_batch.sh <campaign-id> <dark-control-ref>" in doc
