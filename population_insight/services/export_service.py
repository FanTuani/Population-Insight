from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from population_insight.config import EXPORT_DIR


def export_to_csv(records: list[dict[str, Any]], output_path: str | None = None) -> str:
    if not records:
        raise ValueError("没有可导出的数据。")

    if output_path:
        path = Path(output_path).expanduser()
        if not path.is_absolute():
            path = EXPORT_DIR / path
    else:
        file_name = f"population_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path = EXPORT_DIR / file_name

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)

    return str(path)
