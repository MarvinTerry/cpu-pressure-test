from __future__ import annotations

import csv
from html import escape
from pathlib import Path
from urllib.parse import quote

PROJECT_ROOT = Path(__file__).resolve().parent
DESCRIPTION_CSV = PROJECT_ROOT / "data" / "DISCRIPTION.csv"
PLOTS_DIR = PROJECT_ROOT / "plots"
IMAGES_DIR = PROJECT_ROOT / "img"
OUTPUT_MD = PROJECT_ROOT / "RESULT.md"
PLOT_IMAGE_HEIGHT_PX = 600
PHOTO_IMAGE_HEIGHT_PX = 400


def load_rows(description_csv: Path) -> list[dict[str, str]]:
    with description_csv.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = []
        for row in reader:
            file_name = (row.get("file_name") or "").strip()
            condition = (row.get("conditioon") or "").strip()
            if not file_name or not condition:
                continue
            rows.append({"file_name": file_name, "condition": condition})
        return rows


def find_plot_path(file_name: str) -> Path:
    csv_path = Path(file_name)
    return PLOTS_DIR / f"{csv_path.stem}.png"


def find_photo_path(condition: str, image_paths: list[Path]) -> Path | None:
    condition_lower = condition.lower()

    exact_stem_matches = [image_path for image_path in image_paths if image_path.stem.lower() in condition_lower]
    if exact_stem_matches:
        return exact_stem_matches[0]

    keyword_aliases = {
        "stock heat sink": ["stock heat sink"],
        "copper heat sink #1": ["copper heat sink #1"],
        "aluminium heat sink #1": ["aluminium heat sink #1"],
        "aluminium heat sink #2": ["aluminium heat sink #2"],
    }

    for image_path in image_paths:
        aliases = keyword_aliases.get(image_path.stem.lower(), [])
        if any(alias in condition_lower for alias in aliases):
            return image_path

    return None


def to_posix_relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def to_markdown_path(path: Path) -> str:
    return quote(to_posix_relative(path), safe='/')


def render_image_tag(path: Path, alt: str, height_px: int) -> str:
    return f'<img src="{to_markdown_path(path)}" alt="{escape(alt)}" height="{height_px}" />'


def build_markdown(rows: list[dict[str, str]], image_paths: list[Path]) -> str:
    lines: list[str] = []
    lines.append("# RESULT")
    lines.append("")
    lines.append("本文件由 `generate_result_md.py` 自动生成，用于汇总每组实验的测试条件、结果图表和对应测试照片。")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| No. | Condition | Plot | Photo |")
    lines.append("| --- | --- | --- | --- |")

    sections: list[str] = []
    for index, row in enumerate(rows, start=1):
        file_name = row["file_name"]
        condition = row["condition"]
        plot_path = find_plot_path(file_name)
        photo_path = find_photo_path(condition, image_paths)

        plot_cell = f"[`{plot_path.name}`]({to_markdown_path(plot_path)})" if plot_path.exists() else "Missing"
        photo_cell = f"[`{photo_path.name}`]({to_markdown_path(photo_path)})" if photo_path else "N/A"
        lines.append(f"| {index} | {condition} | {plot_cell} | {photo_cell} |")

        sections.append(f"## {index}. {condition}")
        sections.append("")
        sections.append(f"- CSV: `{file_name}`")
        sections.append(f"- Plot: `{to_posix_relative(plot_path)}`")
        if photo_path:
            sections.append(f"- Photo: `{to_posix_relative(photo_path)}`")
        else:
            sections.append("- Photo: 暂无对应测试照片")
        sections.append("")

        if plot_path.exists():
            sections.append("### Plot")
            sections.append("")
            sections.append(render_image_tag(plot_path, f"{condition} plot", PLOT_IMAGE_HEIGHT_PX))
            sections.append("")
        else:
            sections.append("> Plot image not found.")
            sections.append("")

        sections.append("### Test Photo")
        sections.append("")
        if photo_path:
            sections.append(render_image_tag(photo_path, f"{condition} photo", PHOTO_IMAGE_HEIGHT_PX))
        else:
            sections.append("暂无对应测试照片。")
        sections.append("")

    return "\n".join(lines + [""] + sections).rstrip() + "\n"


def main() -> int:
    if not DESCRIPTION_CSV.exists():
        raise FileNotFoundError(f"Description CSV not found: {DESCRIPTION_CSV}")

    rows = load_rows(DESCRIPTION_CSV)
    image_paths = sorted(IMAGES_DIR.glob("*")) if IMAGES_DIR.exists() else []
    markdown = build_markdown(rows, image_paths)
    OUTPUT_MD.write_text(markdown, encoding="utf-8")
    print(f"Generated {OUTPUT_MD.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
