from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


STUDY_FILES = {
    "webcam_intensity": "webcam_intensity_by_duty.csv",
    "webcam_exposure": "webcam_parameter_by_exposure.csv",
    "webcam_duration": "webcam_parameter_by_duration.csv",
    "op598_runs": "op598_characterization_runs.csv",
    "op598_duty": "op598_characterization_by_duty.csv",
    "op598_duration": "op598_characterization_by_duration.csv",
    "dual_runs": "dual_random_train_runs.csv",
    "dual_overall": "dual_random_train_overall.csv",
}


def find_repo_root(start: Path | None = None) -> Path:
    candidates = [start.resolve() if start else Path.cwd().resolve(), Path(__file__).resolve().parent]
    for candidate in candidates:
        for parent in [candidate, *candidate.parents]:
            if (parent / ".git").exists() and (parent / "data" / "derived" / "studies").exists():
                return parent
    raise FileNotFoundError("No se pudo ubicar la raiz del repo desde el notebook.")


def setup_notebook_style() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams.update(
        {
            "figure.figsize": (11, 6),
            "axes.titlesize": 16,
            "axes.labelsize": 12,
            "legend.frameon": True,
            "figure.dpi": 120,
        }
    )


def studies_dir(repo_root: Path) -> Path:
    return repo_root / "data" / "derived" / "studies"


def notebook_figure_dir(repo_root: Path) -> Path:
    path = repo_root / "data" / "derived" / "presentation" / "notebook"
    path.mkdir(parents=True, exist_ok=True)
    return path


def reconstruction_dir(repo_root: Path) -> Path:
    path = repo_root / "data" / "derived" / "reconstruction"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_study_tables(repo_root: Path | None = None) -> dict[str, pd.DataFrame]:
    root = find_repo_root(repo_root)
    base = studies_dir(root)
    tables: dict[str, pd.DataFrame] = {}
    for name, filename in STUDY_FILES.items():
        path = base / filename
        if not path.exists():
            raise FileNotFoundError(f"Falta el artefacto derivado requerido: {path}")
        tables[name] = pd.read_csv(path)
    return tables


def describe_sources(repo_root: Path, tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    base = studies_dir(repo_root)
    rows = []
    for name, filename in STUDY_FILES.items():
        rows.append(
            {
                "tabla": name,
                "archivo": str((base / filename).relative_to(repo_root)),
                "filas": int(len(tables[name])),
                "columnas": int(len(tables[name].columns)),
            }
        )
    return pd.DataFrame(rows)


def export_figure(fig: plt.Figure, repo_root: Path, filename: str) -> Path:
    path = notebook_figure_dir(repo_root) / filename
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    return path


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def first_row_at_least(frame: pd.DataFrame, column: str, threshold: float) -> pd.Series | None:
    matches = frame.loc[frame[column] >= threshold]
    if matches.empty:
        return None
    return matches.sort_values(column).iloc[0]


def success_runs(frame: pd.DataFrame, threshold: float = 0.8) -> pd.DataFrame:
    return frame.loc[frame["coincidence_success_rate_windowed"] >= threshold].copy()
