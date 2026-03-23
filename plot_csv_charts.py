from __future__ import annotations

import math
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
MPL_CONFIG_DIR = PROJECT_ROOT / ".cache" / "matplotlib"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CONFIG_DIR))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator
import pandas as pd


TIME_COLUMN = "Time"
TEMP_COLUMN = "Temp:Soc_Thermal,0"
FREQ_COLUMNS = ["Frequency:Core 0", "Frequency:Core 1", "Frequency:Core 2"]
UTIL_COLUMN = "Util:Avg"
PLOT_COLUMNS = [TEMP_COLUMN, *FREQ_COLUMNS, UTIL_COLUMN]
DESCRIPTION_CSV = "DISCRIPTION.csv"
SUBPLOT_HEIGHT_RATIOS = [1, 1, 1 / 3]
SECONDS_PER_MINUTE = 60
UTIL_START_THRESHOLD = 90.0


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


def get_plot_start_time(df: pd.DataFrame) -> pd.Timestamp:
    start_rows = df[df[UTIL_COLUMN] >= UTIL_START_THRESHOLD]
    if start_rows.empty:
        return df[TIME_COLUMN].iloc[0]
    return start_rows[TIME_COLUMN].iloc[0]


def trim_df_for_plot(df: pd.DataFrame) -> pd.DataFrame:
    start_time = get_plot_start_time(df)
    return df[df[TIME_COLUMN] >= start_time].copy()


def get_elapsed_seconds(df: pd.DataFrame) -> pd.Series:
    return (df[TIME_COLUMN] - df[TIME_COLUMN].iloc[0]).dt.total_seconds()


def get_axis_duration_seconds(dataframes: list[pd.DataFrame]) -> float:
    max_duration_seconds = max(get_elapsed_seconds(df).iloc[-1] for df in dataframes)
    rounded_minutes = math.ceil(max_duration_seconds / SECONDS_PER_MINUTE)
    return max(SECONDS_PER_MINUTE, rounded_minutes * SECONDS_PER_MINUTE)


def format_elapsed_time(value: float, _: float) -> str:
    total_minutes = max(0, int(round(value / SECONDS_PER_MINUTE)))
    hours, minutes = divmod(total_minutes, 60)
    return f"{hours:02d}:{minutes:02d}"


def plot_csv(
    csv_path: Path,
    df: pd.DataFrame,
    output_dir: Path,
    descriptions: dict[str, str],
    axis_duration_seconds: float,
) -> Path:
    title = descriptions.get(csv_path.name) or descriptions.get(str(csv_path.relative_to(PROJECT_ROOT))) or csv_path.stem
    elapsed_seconds = get_elapsed_seconds(df)

    fig, axes = plt.subplots(
        3,
        1,
        figsize=(16, 8),
        sharex=True,
        constrained_layout=True,
        gridspec_kw={"height_ratios": SUBPLOT_HEIGHT_RATIOS},
    )
    fig.suptitle(title, fontsize=14)

    axes[0].plot(elapsed_seconds, df[TEMP_COLUMN], color="#d1495b", linewidth=1.8)
    axes[0].set_ylabel(TEMP_COLUMN)
    axes[0].grid(True, alpha=0.3)

    for column, color in zip(FREQ_COLUMNS, ["#00798c", "#edae49", "#30638e"]):
        axes[1].plot(elapsed_seconds, df[column], label=column, linewidth=1.6, color=color)
    axes[1].set_ylabel("Frequency")
    axes[1].legend(loc="upper right")
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(elapsed_seconds, df[UTIL_COLUMN], color="#2a9d8f", linewidth=1.8)
    axes[2].set_ylabel(UTIL_COLUMN)
    axes[2].set_xlabel("Elapsed Time Since Util:Avg First Reached 90% (HH:MM)")
    axes[2].grid(True, alpha=0.3)

    for axis in axes:
        axis.set_xlim(0, axis_duration_seconds)
        axis.xaxis.set_major_locator(MultipleLocator(SECONDS_PER_MINUTE))
        axis.xaxis.set_major_formatter(FuncFormatter(format_elapsed_time))
    axes[2].tick_params(axis="x", rotation=45)

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

    loaded_data = [(csv_file, trim_df_for_plot(load_csv(csv_file))) for csv_file in csv_files]
    axis_duration_seconds = get_axis_duration_seconds([df for _, df in loaded_data])

    for csv_file, df in loaded_data:
        output_path = plot_csv(csv_file, df, output_dir, descriptions, axis_duration_seconds)
        print(f"Generated {output_path.relative_to(project_root)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
