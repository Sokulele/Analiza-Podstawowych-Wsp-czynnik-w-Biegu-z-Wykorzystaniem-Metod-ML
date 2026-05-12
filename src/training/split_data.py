"""Podział datasetu keypoints per filmik na train/val/test.

Bazuje na CSV z data/keypoints/ (z kolumną `phase`).
Output: data/splits.json — listy plików per split + statystyki klas.

Zasady (zgodnie z CLAUDE.md / briefem):
- Podział PER FILMIK, nie per klatka (dopiero przez to model generalizuje między biegaczami)
- Ten sam biegacz nie może być w train i test (02/03 to ten sam biegacz — 03 w val, 02 w test)
- Slow-motion filmiki są pełnoprawnym materiałem (model uczy się pozycji, nie timingów)
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Identyfikator = substring występujący w nazwie pliku CSV.
# Każdy wzorzec MUSI być unikalny (skrypt rzuci błąd jeśli pasuje 0 lub >1 plików).
SPLITS_CONFIG: dict[str, list[str]] = {
    "train": [
        "01 - Slow Motion",
        "06 - Running on a treadmill",
        "08 - Treadmill Running Technique - How to run safely on a treadmill.__segment_1",
        "08 - Treadmill Running Technique - How to run safely on a treadmill.__segment_2",
        "SAGE CANADAY TREADMILL TECHNIQUE__segment_3__cropped__segment_1",
        "15 - Mechanics",
        "19 - Barefoot",
        "23 - Pawel",
        "24 - Adam",
        "Running at 4ms",
    ],
    "val": [
        "03 - Running at 15km",
        "SAGE CANADAY TREADMILL TECHNIQUE__segment_3__cropped__segment_2",
    ],
    "test": [
        "02 - Running at 13km",
        "20 - Running",
        "22 - Running Analysis",
    ],
}


def find_csv(keypoints_dir: Path, pattern: str) -> Path:
    """Znajdź dokładnie jeden plik CSV pasujący do substringu `pattern`."""
    matches = [
        p for p in keypoints_dir.glob("*.csv")
        if pattern in p.name and not p.name.startswith("_")
    ]
    if len(matches) == 0:
        raise FileNotFoundError(f"Brak CSV pasującego do wzorca: {pattern!r}")
    if len(matches) > 1:
        names = [p.name for p in matches]
        raise RuntimeError(f"Wzorzec {pattern!r} pasuje do wielu plików: {names}")
    return matches[0]


def count_phases(csv_path: Path) -> tuple[int, dict[str, int]]:
    """Zwróć (liczba_klatek_z_etykietą, rozkład_klas)."""
    df = pd.read_csv(csv_path, usecols=["phase"])
    df = df.dropna(subset=["phase"])
    return len(df), {str(k): int(v) for k, v in df["phase"].value_counts().items()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Podział datasetu na train/val/test per filmik")
    parser.add_argument("--keypoints-dir", type=Path, default=Path("data/keypoints"))
    parser.add_argument("--output", type=Path, default=Path("data/splits.json"))
    args = parser.parse_args()

    # Sprawdzenie czy żaden plik nie jest w dwóch splitach (bezpiecznik przed literówką).
    seen: set[str] = set()
    for split, patterns in SPLITS_CONFIG.items():
        for p in patterns:
            if p in seen:
                raise ValueError(f"Wzorzec {p!r} powtarza się w SPLITS_CONFIG")
            seen.add(p)

    resolved: dict[str, list[str]] = {}
    stats: dict[str, dict] = {}

    for split, patterns in SPLITS_CONFIG.items():
        files: list[str] = []
        total_frames = 0
        class_counts: dict[str, int] = {}
        for pat in patterns:
            csv_path = find_csv(args.keypoints_dir, pat)
            n, classes = count_phases(csv_path)
            files.append(csv_path.name)
            total_frames += n
            for cls, cnt in classes.items():
                class_counts[cls] = class_counts.get(cls, 0) + cnt
            log.info(f"[{split}] {csv_path.name}: {n} klatek {classes}")
        resolved[split] = files
        stats[split] = {
            "n_files": len(files),
            "frames": total_frames,
            "per_class": class_counts,
        }

    total_frames_all = sum(s["frames"] for s in stats.values())
    log.info(f"RAZEM: {total_frames_all} klatek")
    for split, s in stats.items():
        pct = 100.0 * s["frames"] / total_frames_all if total_frames_all else 0.0
        log.info(f"  {split}: {s['n_files']} plików, {s['frames']} klatek ({pct:.1f}%), {s['per_class']}")

    output = {"splits": resolved, "stats": stats}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info(f"Zapisano podział do {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
