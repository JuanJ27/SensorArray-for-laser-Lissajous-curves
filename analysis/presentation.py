from __future__ import annotations

from pathlib import Path


def _try_import_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        return plt
    except Exception:
        return None


def build_presentation_plots(
    output_dir: Path,
    webcam_intensity_rows: list[dict[str, object]],
    webcam_exposure_rows: list[dict[str, object]],
    webcam_duration_rows: list[dict[str, object]],
    op598_duty_rows: list[dict[str, object]],
    dual_run_rows: list[dict[str, object]],
) -> list[str]:
    plt = _try_import_matplotlib()
    if plt is None:
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    def save_current(filename: str) -> None:
        path = output_dir / filename
        plt.tight_layout()
        plt.savefig(path, dpi=160)
        plt.close()
        written.append(str(path))

    if webcam_intensity_rows:
        rows = sorted(webcam_intensity_rows, key=lambda row: float(row["duty"]))
        plt.figure(figsize=(6.5, 4.0))
        plt.plot(
            [float(row["duty"]) for row in rows],
            [float(row["mean_detection_probability"]) for row in rows],
            marker="o",
        )
        plt.ylim(-0.05, 1.05)
        plt.grid(True, alpha=0.3)
        plt.title("Probabilidad de deteccion webcam vs duty")
        plt.xlabel("Duty PWM")
        plt.ylabel("Probabilidad de deteccion")
        save_current("webcam_intensity_detection_probability.png")

    if webcam_exposure_rows:
        plt.figure(figsize=(6.5, 4.0))
        duty_labels = sorted({str(row["duty"]) for row in webcam_exposure_rows})
        for duty_label in duty_labels:
            duty_rows = [row for row in webcam_exposure_rows if str(row["duty"]) == duty_label]
            duty_rows.sort(key=lambda row: float(row["exposure"]))
            plt.plot(
                [float(row["exposure"]) for row in duty_rows],
                [float(row["mean_detection_probability"]) for row in duty_rows],
                marker="o",
                label=f"duty {duty_label}",
            )
        plt.ylim(-0.05, 1.05)
        plt.grid(True, alpha=0.3)
        plt.title("Probabilidad de deteccion vs exposicion")
        plt.xlabel("Exposicion")
        plt.ylabel("Probabilidad de deteccion")
        plt.legend()
        save_current("webcam_exposure_detection_probability.png")

    if webcam_duration_rows:
        plt.figure(figsize=(6.5, 4.0))
        duty_labels = sorted({str(row["duty"]) for row in webcam_duration_rows})
        for duty_label in duty_labels:
            duty_rows = [row for row in webcam_duration_rows if str(row["duty"]) == duty_label]
            duty_rows.sort(key=lambda row: float(row["duration_ms"]))
            plt.plot(
                [float(row["duration_ms"]) for row in duty_rows],
                [float(row["mean_detection_probability"]) for row in duty_rows],
                marker="o",
                label=f"duty {duty_label}",
            )
        plt.ylim(-0.05, 1.05)
        plt.grid(True, alpha=0.3)
        plt.title("Probabilidad de deteccion vs duracion del pulso")
        plt.xlabel("Duracion del pulso (ms)")
        plt.ylabel("Probabilidad de deteccion")
        plt.legend()
        save_current("webcam_duration_detection_probability.png")

    if op598_duty_rows:
        rows = sorted(op598_duty_rows, key=lambda row: float(row["duty"]))
        colors = ["tab:red" if str(row["all_saturated"]).lower() == "true" else "tab:blue" for row in rows]
        plt.figure(figsize=(6.5, 4.0))
        plt.bar([str(row["duty"]) for row in rows], [float(row["mean_peak_adc"]) for row in rows], color=colors)
        plt.axhline(4095.0, color="black", linestyle="--", linewidth=1)
        plt.title("Pico OP598 por duty")
        plt.xlabel("Duty PWM")
        plt.ylabel("Pico ADC medio")
        save_current("op598_peak_by_duty.png")

    if dual_run_rows:
        rows = sorted(dual_run_rows, key=lambda row: str(row["run_id"]))
        plt.figure(figsize=(8.0, 4.0))
        plt.bar(
            [str(row["run_id"]).replace("random-train_", "") for row in rows],
            [float(row["coincidence_success_rate_windowed"]) for row in rows],
        )
        plt.ylim(-0.05, 1.05)
        plt.xticks(rotation=45, ha="right")
        plt.grid(True, axis="y", alpha=0.3)
        plt.title("Tasa de coincidencia por corrida")
        plt.xlabel("Corrida")
        plt.ylabel("Exito de coincidencia en ventanas cubiertas")
        save_current("dual_coincidence_success_rate.png")

    return written
