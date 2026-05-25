from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import nbformat as nbf


REPO_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK_PATH = REPO_ROOT / "notebooks" / "flash_detection_presentation_analysis.ipynb"


def md(text: str) -> nbf.NotebookNode:
    return nbf.v4.new_markdown_cell(dedent(text).strip() + "\n")


def code(text: str) -> nbf.NotebookNode:
    return nbf.v4.new_code_cell(dedent(text).strip() + "\n")


def build_notebook() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    nb.metadata.update(
        {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "file_extension": ".py"},
        }
    )

    nb.cells = [
        md(
            """
            # Material de presentacion: detectabilidad de flashes

            Este cuaderno sintetiza el material offline ya derivado en `data/derived/studies/` para exponer el estado experimental del proyecto.

            **Objetivo cientifico**
            - Evaluar hasta donde la cadena experimental actual permite detectar destellos LED cortos.
            - Comparar lo que aporta la webcam frente al canal analogico con OP598.
            - Mostrar que el flujo dual ya permite medir coincidencia entre ambos canales.

            **Marco de interpretacion**
            - El montaje con LED rojo funciona como analogo controlado de detectabilidad, no como replica completa de una curva de Lissajous real.
            - La webcam USB NO es una camara de alta velocidad.
            - El camino OP598 + ESP32 + MicroPython entrega tiempos practicos utiles, pero con resolucion temporal gruesa para pulsos rapidos.
            """
        ),
        code(
            """
            from pathlib import Path
            import sys

            import matplotlib.pyplot as plt
            import pandas as pd
            import seaborn as sns
            from IPython.display import Image as DisplayImage, Markdown, display

            CANDIDATES = [Path.cwd().resolve(), Path.cwd().resolve().parent]
            REPO_ROOT = None
            for candidate in CANDIDATES:
                if (candidate / ".git").exists() and (candidate / "analysis").exists():
                    REPO_ROOT = candidate
                    break
            if REPO_ROOT is None:
                raise RuntimeError("No se pudo ubicar la raiz del repo para importar modulos de analisis.")

            if str(REPO_ROOT) not in sys.path:
                sys.path.insert(0, str(REPO_ROOT))

            from analysis.presentation_notebook import (
                describe_sources,
                export_figure,
                find_repo_root,
                format_percent,
                load_study_tables,
                reconstruction_dir,
                setup_notebook_style,
                success_runs,
            )

            setup_notebook_style()
            REPO_ROOT = find_repo_root(REPO_ROOT)
            tables = load_study_tables(REPO_ROOT)

            webcam_intensity = tables["webcam_intensity"]
            webcam_exposure = tables["webcam_exposure"]
            webcam_duration = tables["webcam_duration"]
            op598_runs = tables["op598_runs"]
            op598_duty = tables["op598_duty"]
            op598_duration = tables["op598_duration"]
            dual_runs = tables["dual_runs"]
            dual_overall = tables["dual_overall"]
            reconstruction_base = reconstruction_dir(REPO_ROOT)

            print(f"Repo root: {REPO_ROOT}")
            print(f"Tablas derivadas cargadas: {len(tables)}")
            """
        ),
        md(
            """
            ## Fuentes de datos usadas

            El notebook se apoya en artefactos ya agregados por la pipeline offline. Eso reduce friccion al re-ejecutarlo y evita depender de archivos crudos dispersos.
            """
        ),
        code(
            """
            sources = describe_sources(REPO_ROOT, tables)
            display(sources)

            display(
                Markdown(
                    "**Takeaway.** Todo el analisis de esta presentacion sale de `data/derived/studies/`; si esos CSV se regeneran con `python scripts/build_study_summaries.py`, el cuaderno queda actualizado sin tocar hardware."
                )
            )
            """
        ),
        md(
            """
            ## Detectabilidad webcam vs duty

            Primera pregunta: con la configuracion actual, que nivel de excitacion LED empieza a producir deteccion confiable en la webcam?
            """
        ),
        code(
            """
            fig, ax = plt.subplots(figsize=(10, 5.5))
            sns.lineplot(
                data=webcam_intensity,
                x="duty",
                y="mean_detection_probability",
                marker="o",
                linewidth=2.5,
                ax=ax,
            )
            ax.set_ylim(-0.05, 1.05)
            ax.set_title("Detectabilidad media de la webcam segun duty PWM")
            ax.set_xlabel("Duty PWM")
            ax.set_ylabel("Probabilidad media de deteccion")
            ax.axvline(6, color="tab:red", linestyle="--", linewidth=1.5, label="Primer duty con deteccion consistente")
            ax.legend()
            display(webcam_intensity)
            display(fig)
            export_figure(fig, REPO_ROOT, "webcam_detectability_vs_duty.png")
            plt.close(fig)

            threshold = webcam_intensity.loc[webcam_intensity["mean_detection_probability"] >= 0.5].sort_values("duty").iloc[0]
            display(
                Markdown(
                    f"**Takeaway.** En estas corridas heredadas, la webcam pasa de no detectar nada en `duty 1-4` a detectar de forma consistente desde `duty {int(threshold['duty'])}`. Esto habla de detectabilidad del pipeline webcam + umbral, NO de una ley radiometrica del LED."
                )
            )
            """
        ),
        md(
            """
            ## Detectabilidad webcam vs duracion y exposicion

            Ahora separamos dos perillas experimentales distintas:
            - `duracion_ms`: cuanto dura el pulso LED.
            - `exposure`: cuanto integra la webcam cada cuadro.

            La idea es mostrar donde aparece detectabilidad, y donde esa detectabilidad puede venir de integrar mas luz en el frame en vez de resolver mejor el instante del pulso.
            """
        ),
        code(
            """
            fig, axes = plt.subplots(1, 2, figsize=(15, 5.5), sharey=True)

            sns.lineplot(
                data=webcam_duration,
                x="duration_ms",
                y="mean_detection_probability",
                hue="duty",
                marker="o",
                linewidth=2.2,
                palette="deep",
                ax=axes[0],
            )
            axes[0].set_title("Detectabilidad webcam vs duracion del pulso")
            axes[0].set_xlabel("Duracion del pulso (ms)")
            axes[0].set_ylabel("Probabilidad media de deteccion")
            axes[0].set_ylim(-0.05, 1.05)

            sns.lineplot(
                data=webcam_exposure,
                x="exposure",
                y="mean_detection_probability",
                hue="duty",
                marker="o",
                linewidth=2.2,
                palette="deep",
                ax=axes[1],
            )
            axes[1].set_title("Detectabilidad webcam vs exposicion")
            axes[1].set_xlabel("Exposicion solicitada")
            axes[1].set_ylabel("")
            axes[1].set_ylim(-0.05, 1.05)

            display(fig)
            export_figure(fig, REPO_ROOT, "webcam_duration_exposure_summary.png")
            plt.close(fig)

            duration_thresholds = (
                webcam_duration.loc[webcam_duration["mean_detection_probability"] >= 0.5]
                .sort_values(["duty", "duration_ms"])
                .groupby("duty", as_index=False)
                .first()[["duty", "duration_ms", "mean_detection_probability"]]
            )
            display(duration_thresholds)

            low_exposure_gap = webcam_exposure.loc[
                (webcam_exposure["duty"] == 8) & (webcam_exposure["exposure"] <= 5),
                ["exposure", "mean_detection_probability"],
            ]
            display(low_exposure_gap)

            duty6 = duration_thresholds.loc[duration_thresholds["duty"] == 6, "duration_ms"].iloc[0]
            duty8 = duration_thresholds.loc[duration_thresholds["duty"] == 8, "duration_ms"].iloc[0]
            display(
                Markdown(
                    f"**Takeaway.** Para la webcam, los pulsos cortos siguen siendo dificiles: la primera condicion >=50% aparece en `duty 6` recien a `{int(duty6)} ms`, y en `duty 8` a `{int(duty8)} ms`. Subir exposicion ayuda a que aparezca el destello en el frame, pero no convierte a la webcam en un sensor temporal rapido."
                )
            )
            """
        ),
        md(
            """
            ## Caracterizacion OP598 y saturacion

            El canal analogico con OP598 aporta una vista distinta: amplitud ADC, ancho efectivo del pulso reconstruido y una referencia temporal practica de la cadena numerica.
            """
        ),
        code(
            """
            fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))

            saturation_labels = op598_duty["all_saturated"].astype(str).str.lower()
            duty_colors = saturation_labels.map({"true": "tab:red", "false": "tab:blue"})
            axes[0].bar(op598_duty["duty"].astype(str), op598_duty["mean_peak_adc"], color=duty_colors)
            axes[0].axhline(4095, color="black", linestyle="--", linewidth=1.2)
            axes[0].set_title("Pico ADC medio del OP598 por duty")
            axes[0].set_xlabel("Duty PWM")
            axes[0].set_ylabel("Pico ADC medio")

            sns.lineplot(
                data=op598_duration,
                x="duration_ms",
                y="mean_pulse_width_ms",
                marker="o",
                linewidth=2.5,
                ax=axes[1],
            )
            axes[1].set_title("Ancho efectivo medido vs duracion solicitada")
            axes[1].set_xlabel("Duracion solicitada (ms)")
            axes[1].set_ylabel("Ancho efectivo reconstruido (ms)")

            display(fig)
            export_figure(fig, REPO_ROOT, "op598_saturation_and_width.png")
            plt.close(fig)

            sample_interval_ms = op598_runs["sample_interval_avg_ms"].dropna().mean()
            first_saturated = op598_duty.loc[saturation_labels == "true"].sort_values("duty").iloc[0]
            display(op598_duty)
            display(op598_duration)
            display(
                Markdown(
                    f"**Takeaway.** El canal OP598 muestra respuesta util antes de saturar en `duty 8-32`, pero desde `duty {int(first_saturated['duty'])}` pega al techo de `4095`. Ademas, el muestreo medio observado ronda `{sample_interval_ms:.2f} ms`, asi que el sistema entrega tiempos practicos gruesos bajo MicroPython, no metrologia ultrarrapida del fototransistor."
                )
            )
            """
        ),
        md(
            """
            ## Coincidencia dual entre OP598 y webcam

            La pregunta aqui no es solo si cada canal detecta algo, sino si ambos pueden alinearse corrida por corrida para estudiar coincidencia de eventos.
            """
        ),
        code(
            """
            dual_runs_plot = dual_runs.copy()
            dual_runs_plot["run_short"] = dual_runs_plot["run_id"].str.replace("random-train_", "", regex=False)
            dual_runs_plot["limited_coverage_label"] = dual_runs_plot["limited_coverage"].astype(str).str.lower()

            fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
            sns.barplot(
                data=dual_runs_plot,
                x="run_short",
                y="coincidence_success_rate_windowed",
                hue="limited_coverage_label",
                palette={"false": "tab:blue", "true": "tab:orange"},
                ax=axes[0],
            )
            axes[0].set_ylim(-0.05, 1.05)
            axes[0].set_title("Exito de coincidencia dual por corrida")
            axes[0].set_xlabel("")
            axes[0].set_ylabel("Tasa de exito en ventanas cubiertas")
            axes[0].legend(title="Cobertura limitada")

            sns.barplot(
                data=dual_runs_plot,
                x="run_short",
                y="coverage_fraction",
                color="tab:gray",
                ax=axes[1],
            )
            axes[1].set_ylim(-0.05, 1.05)
            axes[1].set_title("Cobertura de video por corrida")
            axes[1].set_xlabel("Corrida")
            axes[1].set_ylabel("Fraccion de pulsos cubiertos")
            axes[1].tick_params(axis="x", rotation=45)

            display(fig)
            export_figure(fig, REPO_ROOT, "dual_coincidence_and_coverage.png")
            plt.close(fig)

            display(dual_overall)
            best_runs = success_runs(dual_runs).sort_values("coincidence_success_rate_windowed", ascending=False)
            display(best_runs[["run_id", "variant", "coverage_fraction", "coincidence_success_rate_windowed", "mean_offset_ms_detected"]])

            full_coverage = dual_overall.loc[dual_overall["subset"] == "fully_covered_runs", "mean_windowed_success_rate"].iloc[0]
            limited = int((dual_runs["limited_coverage"].astype(str).str.lower() == "true").sum())
            total = int(len(dual_runs))
            display(
                Markdown(
                    f"**Takeaway.** El flujo dual YA permite cuantificar coincidencia: en corridas con cobertura completa, la tasa media de exito en ventanas cubiertas es `{format_percent(full_coverage)}`. Pero hay `{limited}` corrida(s) de `{total}` con video incompleto, y eso obliga a separar exito sobre ventanas cubiertas de exito sobre todos los pulsos."
                )
            )
            """
        ),
        md(
            """
            ## Reconstruccion estadistica y slow motion proxy

            Esta parte SIEMPRE hay que leerla con disciplina conceptual: no estamos viendo video rapido real del flash. Estamos apilando muchas coincidencias buenas para construir una proxy visual acumulada del evento.
            """
        ),
        code(
            """
             selection_path = reconstruction_base / "best_dual_run_selection.csv"
            stats_path = reconstruction_base / "reconstruction_statistics.csv"
            overview_path = reconstruction_base / "reconstruction_overview.md"
            confidence_notes_path = reconstruction_base / "reconstruction_confidence_notes.md"
            uncertainty_path = reconstruction_base / "reconstruction_uncertainty_summary.md"
            avg_frame_path = reconstruction_base / "avg_flash_frame.png"
            heatmap_path = reconstruction_base / "flash_heatmap.png"
            comparison_panel_path = reconstruction_base / "reconstruction_comparison_panel.png"
            offset_distribution_path = reconstruction_base / "coincidence_offset_distribution.png"
            slowmo_path = reconstruction_base / "slowmo_reconstruction.gif"
            pulse_strip_dir = reconstruction_base / "pulse_strips"

            selection = pd.read_csv(selection_path)
            reconstruction_stats = pd.read_csv(stats_path)
            selected = selection.loc[
                selection["selected_for_reconstruction"].astype(str).str.lower() == "true",
                [
                    "selection_rank",
                    "run_id",
                    "variant",
                    "covered_pulses",
                    "matched_detected",
                    "coincidence_success_rate_windowed",
                    "mean_offset_ms_detected",
                ],
            ].sort_values("selection_rank")
            display(selected)
            display(reconstruction_stats.loc[reconstruction_stats["group_id"] == "pooled"])

            fig, axes = plt.subplots(1, 2, figsize=(15, 5.8))
            axes[0].imshow(plt.imread(avg_frame_path))
            axes[0].set_title("Promedio de frames emparejados")
            axes[0].axis("off")

            axes[1].imshow(plt.imread(heatmap_path))
            axes[1].set_title("Mapa acumulado matched - before")
            axes[1].axis("off")

            display(fig)
            plt.close(fig)

            display(DisplayImage(filename=str(comparison_panel_path)))
            display(DisplayImage(filename=str(offset_distribution_path)))

            for strip_path in sorted(pulse_strip_dir.glob("*.png")):
                display(DisplayImage(filename=str(strip_path)))

            display(DisplayImage(filename=str(slowmo_path)))
            display(Markdown(confidence_notes_path.read_text(encoding="utf-8")))
            display(Markdown(uncertainty_path.read_text(encoding="utf-8")))

            display(
                Markdown(
                    "**Takeaway.** La reconstruccion ahora es mas defendible porque junta evidencia visual por fases, comparacion pooled vs por corrida, cantidad de pulsos, IC95% de coincidencia, distribucion de offsets y un resumen explicito de incertidumbre sistematica. Sigue siendo una proxy estadistica, NO filmacion de alta velocidad."
                )
            )
            """
        ),
        md(
            """
            ## Incertidumbre y errores sistematicos

            Si queres defender esto cientificamente, ACA ESTA la parte que no se puede esquivar: cuantizacion temporal webcam, anclaje OP598 bajo MicroPython, sensibilidad al umbral, dependencia con exposicion, saturacion y pocas replicas.
            """
        ),
        code(
            """
            uncertainty_path = reconstruction_base / "reconstruction_uncertainty_summary.md"
            display(Markdown(uncertainty_path.read_text(encoding="utf-8")))
            """
        ),
        md(
            """
            ## Que se puede y que no se puede afirmar

            **Si se puede afirmar con respaldo de estos datos**
            - La detectabilidad de flashes con webcam depende fuertemente de duty, duracion y exposicion.
            - El canal OP598 detecta variaciones utiles a bajo duty, pero satura rapido al crecer la excitacion.
            - El pipeline dual ya permite medir coincidencia entre pulsos LED y frames detectados.
             - La reconstruccion estadistica por coincidencias permite generar una proxy visual acumulada y un slow motion sintetico del evento.
             - La nueva salida de incertidumbre ya no vende precision falsa: expresa CI binomial, sensibilidad al umbral y limites temporales como intervalos practicos.

            **No se debe sobreafirmar**
            - Estos resultados NO prueban todavia deteccion de curvas de Lissajous reales.
             - La webcam NO resuelve dinamica temporal fina como lo haria una camara de alta velocidad.
             - Los tiempos OP598 observados reflejan la cadena `LED + optica + OP598 + ADC + ESP32 + MicroPython`, no la respuesta intrinseca aislada del fototransistor.
             - El GIF reconstruido NO representa frames reales consecutivos de un unico destello; son promedios relativos alrededor de muchas coincidencias.
             - Los umbrales de duty y duracion detectables siguen siendo condicionales al pipeline actual y a pocas replicas.
            """
        ),
        md(
            """
            ## Conclusiones finales y siguiente trabajo

            **Conclusiones**
            - El material derivado actual ya alcanza para una exposicion honesta sobre detectabilidad de destellos.
            - La webcam sirve como evidencia visual y de detectabilidad gruesa, especialmente cuando el pulso es suficientemente largo o la integracion del frame ayuda.
            - El canal OP598 es mejor para seguir la respuesta analogica, aunque hoy esta limitado por saturacion y por el tiempo de muestreo efectivo bajo MicroPython.
            - La coincidencia dual es la pieza mas prometedora para enlazar ambos mundos en futuras defensas del proyecto.
             - La nueva reconstruccion estadistica agrega una pieza de narrativa visual mucho mas clara para presentacion offline, sin vender humo sobre imagen rapida directa.
             - El tratamiento de incertidumbre ahora deja explicito que varias conclusiones deben leerse como rangos practicos y no como precision fisica fina.

            **Proximo trabajo recomendado**
            1. Repetir condiciones clave con mas replicas por punto para mejorar respaldo estadistico.
            2. Diseñar corridas duales con cobertura webcam garantizada de inicio a fin.
            3. Explorar electronica o firmware con mejor resolucion temporal si la pregunta pasa de detectabilidad a temporizacion fina.
            """
        ),
    ]
    return nb


def main() -> int:
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    notebook = build_notebook()
    with NOTEBOOK_PATH.open("w", encoding="utf-8") as handle:
        nbf.write(notebook, handle)
    print(NOTEBOOK_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
