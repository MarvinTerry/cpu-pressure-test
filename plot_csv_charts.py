from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
MPL_CONFIG_DIR = PROJECT_ROOT / ".cache" / "matplotlib"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CONFIG_DIR))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


TIME_COLUMN = "Time"
TEMP_COLUMN = "Temp:Soc_Thermal,0"
FREQ_COLUMNS = ["Frequency:Core 0", "Frequency:Core 1", "Frequency:Core 2"]
UTIL_COLUMN = "Util:Avg"
PLOT_COLUMNS = [TEMP_COLUMN, *FREQ_COLUMNS, UTIL_COLUMN]
DESCRIPTION_CSV = "DISCRIPTION.csv"


def load_descriptions(description_csv: Path) -> dict[str, str]:
    if not description_csv.exists():
        return {}

    df = pd.read_csv(description_csv)
    required_columns = {"file_name", "conditioon"}
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"{description_csv.name} is missing columns: {missing}")

    descriptions: dict[str, str] = {}
    for _, row in df.iterrows():
        file_name = str(row["file_name"]).strip()
        description = str(row["conditioon"]).strip()
        if not file_name or not description:
            continue

        path = Path(file_name)
        descriptions[path.name] = description
        descriptions[file_name] = description

    return descriptions


def load_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    missing_columns = [column for column in [TIME_COLUMN, *PLOT_COLUMNS] if column not in df.columns]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"{csv_path.name} is missing columns: {missing}")

    df[TIME_COLUMN] = pd.to_datetime(df[TIME_COLUMN], format="%Y-%m-%d_%H:%M:%S", errors="coerce")
    if df[TIME_COLUMN].isna().any():
        raise ValueError(f"{csv_path.name} contains invalid values in '{TIME_COLUMN}'")

    return df


def plot_csv(csv_path: Path, output_dir: Path, descriptions: dict[str, str]) -> Path:
    df = load_csv(csv_path)
    title = descriptions.get(csv_path.name) or descriptions.get(str(csv_path.relative_to(PROJECT_ROOT))) or csv_path.stem

    fig, axes = plt.subplots(3, 1, figsize=(16, 10), sharex=True, constrained_layout=True)
    fig.suptitle(title, fontsize=14)

    axes[0].plot(df[TIME_COLUMN], df[TEMP_COLUMN], color="#d1495b", linewidth=1.8)
    axes[0].set_ylabel(TEMP_COLUMN)
    axes[0].grid(True, alpha=0.3)

    for column, color in zip(FREQ_COLUMNS, ["#00798c", "#edae49", "#30638e"]):
        axes[1].plot(df[TIME_COLUMN], df[column], label=column, linewidth=1.6, color=color)
    axes[1].set_ylabel("Frequency")
    axes[1].legend(loc="upper right")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(df[TIME_COLUMN], df[UTIL_COLUMN], color="#2a9d8f", linewidth=1.8)
    axes[2].set_ylabel(UTIL_COLUMN)
    axes[2].set_xlabel(TIME_COLUMN)
    axes[2].grid(True, alpha=0.3)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{csv_path.stem}.png"
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def main() -> int:
    project_root = PROJECT_ROOT
    data_dir = project_root / "data"
    output_dir = project_root / "plots"
    description_csv = data_dir / DESCRIPTION_CSV
    descriptions = load_descriptions(description_csv)

    csv_files = sorted(csv_file for csv_file in data_dir.glob("*.csv") if csv_file.name != DESCRIPTION_CSV)
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    for csv_file in csv_files:
        output_path = plot_csv(csv_file, output_dir, descriptions)
        print(f"Generated {output_path.relative_to(project_root)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
