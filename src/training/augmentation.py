"""Augmentacja danych dla treningu klasyfikatora faz biegu.

Główna funkcja: ``flip_horizontal_dataframe(df)`` — odbicie lustrzane filmiku.
- x' = 1 - x dla wszystkich keypointów (MediaPipe x normalizowany do 0-1)
- y, z, visibility — bez zmian (lustro nie zmienia anatomii — MediaPipe oznaczyłby
  te same keypointy jako LEFT/RIGHT zgodnie z anatomią biegacza)
- etykiety: LEFT_STANCE ↔ RIGHT_STANCE, FLIGHT bez zmian
  (konwencja CSV po `auto_label.swap_left_right` — etykieta zależy od kierunku biegu,
  który flip odwraca, więc etykiety muszą być przemapowane)

UWAGA — historia decyzji metodologicznej (2026-05-08):
Pierwsza wersja swap'owała LEFT_xxx ↔ RIGHT_xxx keypointy (16 par). Skutek: regresja
RF v1 z 62.7% do 53.7% test acc (−9 p.p.). Powód: w CSV `LEFT_HIP_x` zawsze odpowiada
**anatomicznie** lewemu biodru biegacza (MediaPipe konwencja, niezależna od kierunku).
Swap L/R keypointów dawał chaos — model uczył się że ta sama kolumna ma dwa różne
znaczenia anatomiczne. Naprawione: keypointy NIE są swap'owane, tylko x' = 1 - x.

Flip horyzontalny to standardowa augmentacja w pose estimation (OpenPose, AlphaPose).
W kontekście biegu na bieżni z bocznego ujęcia jest fizycznie sensowny — model staje się
symetryczny dla biegaczy zwróconych w lewo i w prawo, co jest pożądane biomechanicznie.

Uruchomienie standalone (sanity check):
    python -m src.training.augmentation --csv "data/keypoints/02 - Running at 13km⧸h - Side View.csv"
"""
from __future__ import annotations

import pandas as pd

# 16 par symetrycznych landmarków MediaPipe Pose (LEFT_xxx ↔ RIGHT_xxx)
SYMMETRIC_PAIRS: list[tuple[str, str]] = [
    ("LEFT_EYE_INNER", "RIGHT_EYE_INNER"),
    ("LEFT_EYE", "RIGHT_EYE"),
    ("LEFT_EYE_OUTER", "RIGHT_EYE_OUTER"),
    ("LEFT_EAR", "RIGHT_EAR"),
    ("MOUTH_LEFT", "MOUTH_RIGHT"),
    ("LEFT_SHOULDER", "RIGHT_SHOULDER"),
    ("LEFT_ELBOW", "RIGHT_ELBOW"),
    ("LEFT_WRIST", "RIGHT_WRIST"),
    ("LEFT_PINKY", "RIGHT_PINKY"),
    ("LEFT_INDEX", "RIGHT_INDEX"),
    ("LEFT_THUMB", "RIGHT_THUMB"),
    ("LEFT_HIP", "RIGHT_HIP"),
    ("LEFT_KNEE", "RIGHT_KNEE"),
    ("LEFT_ANKLE", "RIGHT_ANKLE"),
    ("LEFT_HEEL", "RIGHT_HEEL"),
    ("LEFT_FOOT_INDEX", "RIGHT_FOOT_INDEX"),
]

# Mapowanie etykiet faz biegu po flip'ie horyzontalnym
PHASE_FLIP_MAP: dict[str, str] = {
    "LEFT_STANCE": "RIGHT_STANCE",
    "RIGHT_STANCE": "LEFT_STANCE",
    "FLIGHT": "FLIGHT",
    "DOUBLE_SUPPORT": "DOUBLE_SUPPORT",
}

# Atrybuty per landmark (kolumny CSV: {LANDMARK}_{ATTR})
ATTRS: tuple[str, ...] = ("x", "y", "z", "visibility")


def flip_horizontal_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Zwraca nową kopię DataFrame'u z odbiciem lustrzanym keypointów + zamianą etykiet phase.

    Wejście: df z keypointami MediaPipe (kolumny `{LANDMARK}_{x|y|z|visibility}`)
    oraz opcjonalnie kolumnami `phase` i `phase_auto`.

    Operacje:
    1. x' = 1 - x dla wszystkich kolumn `_x` (MediaPipe normalizuje x do [0,1] względem szerokości kadru)
    2. y, z, visibility — bez zmian (anatomia keypointów nie zmienia się przy fliplie)
    3. Etykiety phase i phase_auto: LEFT_STANCE ↔ RIGHT_STANCE (konwencja CSV
       zależy od kierunku biegu, który flip odwraca)

    NIE swap'ujemy LEFT_xxx ↔ RIGHT_xxx keypointów — szczegóły w docstring modułu.
    """
    out = df.copy()

    # Krok 1: x' = 1 - x dla wszystkich keypointów
    x_cols = [c for c in out.columns if c.endswith("_x")]
    for col in x_cols:
        out[col] = 1.0 - out[col]

    # Krok 2: zamiana etykiet faz (LEFT↔RIGHT, FLIGHT bez zmian)
    for phase_col in ("phase", "phase_auto"):
        if phase_col in out.columns:
            out[phase_col] = out[phase_col].map(PHASE_FLIP_MAP)

    return out


def _sanity_check(csv_path: str) -> None:
    """Sanity check: wczytaj CSV, flip dwa razy, sprawdź czy wracamy do oryginału."""
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    df_flipped = flip_horizontal_dataframe(df)
    df_double = flip_horizontal_dataframe(df_flipped)

    # Numeryczne kolumny powinny się odtworzyć
    num_cols = [c for c in df.columns if c.endswith(tuple(f"_{a}" for a in ATTRS))]
    diff = (df[num_cols] - df_double[num_cols]).abs().max().max()
    print(f"Max abs diff po podwójnym flipie: {diff:.6e} (oczekiwane ~0)")

    # Etykiety phase powinny być zachowane po podwójnym flipie
    if "phase" in df.columns:
        same = (df["phase"].values == df_double["phase"].values).all()
        print(f"Etykiety phase identyczne po podwójnym flipie: {same}")

    # Po fliplie x' = 1 - x dla każdej kolumny _x (bez swap'a L/R)
    # NOSE: suma orig+flip = 1.0 (zawsze)
    if "NOSE_x" in df.columns:
        sums = df["NOSE_x"].values + df_flipped["NOSE_x"].values
        print(f"NOSE_x suma orig+flip: {sums.min():.4f}–{sums.max():.4f} (oczekiwane 1.0)")

    # LEFT_HIP_x_flip == 1 - LEFT_HIP_x_orig (ta sama anatomiczna noga, lustrzana pozycja)
    if "LEFT_HIP_x" in df.columns:
        diff = (df_flipped["LEFT_HIP_x"].values - (1.0 - df["LEFT_HIP_x"].values)).max()
        print(f"LEFT_HIP_x_flip == 1 - LEFT_HIP_x_orig: max_diff={abs(diff):.2e} (oczekiwane ~0)")

    # LEFT_HIP_y bez zmian (flip horyzontalny nie zmienia y)
    if "LEFT_HIP_y" in df.columns:
        diff = (df_flipped["LEFT_HIP_y"].values - df["LEFT_HIP_y"].values).max()
        print(f"LEFT_HIP_y_flip == LEFT_HIP_y_orig: max_diff={abs(diff):.2e} (oczekiwane 0)")

    # Etykiety: w pojedynczym flipie LEFT_STANCE → RIGHT_STANCE
    if "phase" in df.columns:
        n_left_orig = (df["phase"] == "LEFT_STANCE").sum()
        n_right_flip = (df_flipped["phase"] == "RIGHT_STANCE").sum()
        print(f"LEFT_STANCE w oryginale: {n_left_orig}, RIGHT_STANCE we flippie: {n_right_flip} (oczekiwane równe)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sanity check augmentacji flip horyzontalny")
    parser.add_argument("--csv", required=True, help="Ścieżka do CSV z keypointami do testu")
    args = parser.parse_args()
    _sanity_check(args.csv)
