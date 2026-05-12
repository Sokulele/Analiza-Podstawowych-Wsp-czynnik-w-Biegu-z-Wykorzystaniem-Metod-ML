"""Feature engineering — cechy antropometryczne z keypointów MediaPipe.

Trzy główne problemy jakie rozwiązuje ten moduł:

1. **Kadrowanie** — surowe (x, y) z MediaPipe są znormalizowane względem CAŁEGO kadru.
   Tu centrujemy je na mid_hip (środek bioder) i skalujemy długością tułowia.
   Efekt: cechy nie zależą od pozycji biegacza w kadrze ani od wzrostu.

2. **Reprezentacja biomechaniczna** — zamiast polegać tylko na surowych współrzędnych,
   obliczamy kąty stawów (kolana, biodra, kostki) i pochylenie tułowia.
   Te cechy mają bezpośredni sens biomechaniczny (literatura).

3. **Aspect ratio fix (apply_aspect_ratio_correction)** — MediaPipe normalizuje x i y
   OSOBNO do [0,1] (każda oś względem wymiaru kadru). Dla filmów nie-kwadratowych
   jednostki x i y nie są spójne fizycznie. Funkcja `apply_aspect_ratio_correction`
   mnoży x*width, y*height — po niej `torso_length = sqrt(dx²+dy²)` jest w pikselach
   (spójne jednostki). Bug zidentyfikowany na filmie 22 (608×1080, pionowy).

Moduł jest reużywalny — używany przez `train_rf_v2.py`, `train_lstm.py`, oraz przez
skrypty inferencyjne (`postprocess_median.py`, `ensemble.py`).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

# 33 keypointy MediaPipe (kolejność zgodna z PoseLandmark enum)
KEYPOINT_NAMES: list[str] = [
    "NOSE", "LEFT_EYE_INNER", "LEFT_EYE", "LEFT_EYE_OUTER",
    "RIGHT_EYE_INNER", "RIGHT_EYE", "RIGHT_EYE_OUTER",
    "LEFT_EAR", "RIGHT_EAR", "MOUTH_LEFT", "MOUTH_RIGHT",
    "LEFT_SHOULDER", "RIGHT_SHOULDER", "LEFT_ELBOW", "RIGHT_ELBOW",
    "LEFT_WRIST", "RIGHT_WRIST", "LEFT_PINKY", "RIGHT_PINKY",
    "LEFT_INDEX", "RIGHT_INDEX", "LEFT_THUMB", "RIGHT_THUMB",
    "LEFT_HIP", "RIGHT_HIP", "LEFT_KNEE", "RIGHT_KNEE",
    "LEFT_ANKLE", "RIGHT_ANKLE", "LEFT_HEEL", "RIGHT_HEEL",
    "LEFT_FOOT_INDEX", "RIGHT_FOOT_INDEX",
]

AXES = ("x", "y", "z")


def _col(kp: str, axis: str) -> str:
    return f"{kp}_{axis}"


def _xyz(df: pd.DataFrame, kp: str) -> np.ndarray:
    """Zwróć macierz (N, 3) ze współrzędnymi x,y,z keypointu."""
    return df[[_col(kp, a) for a in AXES]].to_numpy(dtype=np.float32)


def _midpoint(df: pd.DataFrame, kp_a: str, kp_b: str) -> np.ndarray:
    """Środek między dwoma keypointami, shape (N, 3)."""
    return (_xyz(df, kp_a) + _xyz(df, kp_b)) / 2.0


def _angle_deg(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Kąt w punkcie b między wektorami (b→a) i (b→c), w stopniach. Shape (N,).

    Używamy arctan2 z iloczynu wektorowego i skalarnego — stabilne numerycznie,
    nie załamuje się przy wektorach prostopadłych ani równoległych.
    """
    ba = a - b
    bc = c - b
    cross = np.linalg.norm(np.cross(ba, bc), axis=1)
    dot = np.sum(ba * bc, axis=1)
    return np.degrees(np.arctan2(cross, dot))


def compute_engineered_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Zbuduj cechy inżynierowane z DataFrame z surowymi keypointami.

    Zwraca (DataFrame z cechami, lista nazw kolumn cech).

    Cechy (N = liczba klatek w df):
    - 99 znormalizowanych współrzędnych: (x, y, z) dla 33 keypointów,
      wycentrowanych na mid_hip i przeskalowanych długością tułowia
    - 6 kątów stawów: kolana (L/R), biodra (L/R), kostki (L/R)
    - 1 pochylenie tułowia względem pionu
    = 106 cech łącznie

    UWAGA: zakładamy, że df ma już zapewnione pose_detected=1 (filtr wcześniej).
    """
    # Normalizacja: centrujemy na mid_hip, skalujemy długością tułowia
    mid_hip = _midpoint(df, "LEFT_HIP", "RIGHT_HIP")          # (N, 3)
    mid_shoulder = _midpoint(df, "LEFT_SHOULDER", "RIGHT_SHOULDER")
    torso_length = np.linalg.norm(mid_shoulder - mid_hip, axis=1)  # (N,)
    # Bezpiecznik: torso nigdy nie powinno być 0, ale gdyby keypointy były zdegenerowane
    torso_length = np.where(torso_length < 1e-6, 1.0, torso_length)

    out = {}
    feature_cols: list[str] = []

    # Znormalizowane współrzędne wszystkich keypointów
    for kp in KEYPOINT_NAMES:
        xyz = _xyz(df, kp)                                    # (N, 3)
        normalized = (xyz - mid_hip) / torso_length[:, None]  # (N, 3)
        for i, axis in enumerate(AXES):
            name = f"{kp}_{axis}_norm"
            out[name] = normalized[:, i]
            feature_cols.append(name)

    # Kąty stawów (biomechaniczne)
    # Kolano: biodro → kolano → kostka
    out["left_knee_angle"] = _angle_deg(
        _xyz(df, "LEFT_HIP"), _xyz(df, "LEFT_KNEE"), _xyz(df, "LEFT_ANKLE")
    )
    out["right_knee_angle"] = _angle_deg(
        _xyz(df, "RIGHT_HIP"), _xyz(df, "RIGHT_KNEE"), _xyz(df, "RIGHT_ANKLE")
    )
    # Biodro: ramię → biodro → kolano
    out["left_hip_angle"] = _angle_deg(
        _xyz(df, "LEFT_SHOULDER"), _xyz(df, "LEFT_HIP"), _xyz(df, "LEFT_KNEE")
    )
    out["right_hip_angle"] = _angle_deg(
        _xyz(df, "RIGHT_SHOULDER"), _xyz(df, "RIGHT_HIP"), _xyz(df, "RIGHT_KNEE")
    )
    # Kostka: kolano → kostka → palce stopy
    out["left_ankle_angle"] = _angle_deg(
        _xyz(df, "LEFT_KNEE"), _xyz(df, "LEFT_ANKLE"), _xyz(df, "LEFT_FOOT_INDEX")
    )
    out["right_ankle_angle"] = _angle_deg(
        _xyz(df, "RIGHT_KNEE"), _xyz(df, "RIGHT_ANKLE"), _xyz(df, "RIGHT_FOOT_INDEX")
    )
    feature_cols.extend([
        "left_knee_angle", "right_knee_angle",
        "left_hip_angle", "right_hip_angle",
        "left_ankle_angle", "right_ankle_angle",
    ])

    # Pochylenie tułowia — kąt linii mid_hip→mid_shoulder względem pionu (osi Y)
    # Im większy, tym bardziej biegacz pochylony do przodu
    torso_vec = mid_shoulder - mid_hip                        # (N, 3)
    # W MediaPipe Y rośnie W DÓŁ, więc pion "do góry" to wektor (0, -1, 0)
    vertical = np.array([0.0, -1.0, 0.0], dtype=np.float32)
    # Używamy tylko komponentów x, y — kąt w płaszczyźnie obrazu
    torso_2d = torso_vec[:, :2]
    vertical_2d = vertical[:2]
    cos_theta = (
        (torso_2d @ vertical_2d)
        / (np.linalg.norm(torso_2d, axis=1) * np.linalg.norm(vertical_2d))
    )
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    out["torso_lean_angle"] = np.degrees(np.arccos(cos_theta))
    feature_cols.append("torso_lean_angle")

    features_df = pd.DataFrame(out, index=df.index)
    return features_df, feature_cols


def apply_aspect_ratio_correction(
    df: pd.DataFrame, width: int, height: int,
) -> pd.DataFrame:
    """Pomnóż wszystkie keypointy x przez width, y przez height (w pikselach).

    MediaPipe Pose normalizuje x i y OSOBNO do [0,1] względem wymiarów kadru.
    Dla filmów nie-kwadratowych skutek: jednostki x i y różnią się fizycznie
    (np. dla 608×1080 pionowego, ten sam Δ=0.1 to 60 pikseli w x ale 108 w y).
    Powoduje to że `torso_length = sqrt((Δhip_x)² + (Δhip_y)²)` jest błędne —
    miesza piksele na różnych osiach.

    Po tej korekcji `_x` i `_y` są w pikselach (jednostka spójna), normalizacja
    przez torso_length dalej daje cechy bezwymiarowe, ale **fizycznie poprawne**.
    Z (głębokość) zostawiamy bez zmian — MediaPipe zwraca z też w przybliżeniu
    znormalizowane do skali x i y, więc poprawiamy go proporcjonalnie do width
    (założenie: x i z są w tej samej skali, MediaPipe konwencja).

    UWAGA: po korekcji wartości `_x` i `_y` NIE są już w [0,1] tylko w pikselach.
    Funkcje pochodne (`flip_horizontal_dataframe` z `x' = 1 - x`) nie powinny być
    aplikowane po tej korekcji.

    Bug zidentyfikowany w sesji 2026-04-26 (LSTM run 1/2 FLIGHT recall 4% na film 22).
    Częściowo zniwelowany przez Pawel/Adam (16:9) w sesji 2026-05-08, ale nadal istotny.
    """
    out = df.copy()
    x_cols = [c for c in out.columns if c.endswith("_x")]
    y_cols = [c for c in out.columns if c.endswith("_y")]
    z_cols = [c for c in out.columns if c.endswith("_z")]
    for c in x_cols:
        out[c] = out[c] * width
    for c in y_cols:
        out[c] = out[c] * height
    # z: MediaPipe konwencja — z jest w skali width (x), więc też * width
    for c in z_cols:
        out[c] = out[c] * width
    return out


def load_video_metadata(metadata_csv: Path) -> dict[str, dict]:
    """Wczytaj `data/videos_metadata.csv` → dict {csv_name: {"width": int, "height": int}}.

    Mapuje nazwę CSV w `data/keypoints/` (np. "02 - Running.csv") na metadane wideo
    (z kolumn `width`, `height`). Konwersja: nazwa wideo z .mp4/.mov → .csv.
    """
    df = pd.read_csv(metadata_csv)
    out: dict[str, dict] = {}
    for _, row in df.iterrows():
        video_name = row["file"]
        csv_name = Path(video_name).with_suffix(".csv").name
        out[csv_name] = {"width": int(row["width"]), "height": int(row["height"])}
    return out


def compute_velocity_features(features_df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Pierwsze różnice znormalizowanych współrzędnych — velocity per klatka per keypoint.

    Operuje na cechach `*_norm` z `compute_engineered_features` — czyli velocity jest
    w jednostkach `torso_length / klatka`, niezależnie od rozmiaru biegacza w kadrze.
    Pierwsza klatka filmu: Δ = 0 (brak poprzedniej klatki).

    Zwraca (DataFrame z 99 cechami velocity, lista nazw kolumn).
    Nazewnictwo: `{KEYPOINT}_{x|y|z}_norm_dt` (suffix `_dt` = "delta time").

    UWAGA: wymaga żeby DataFrame zawierał klatki **z jednego filmiku** w kolejności
    chronologicznej. Jeśli filmiki są skonkatenowane przed wywołaniem, Δ na granicy
    będzie zafałszowane.
    """
    norm_cols = [c for c in features_df.columns if c.endswith("_norm")]
    if not norm_cols:
        raise ValueError("features_df nie zawiera kolumn `*_norm` — czy compute_engineered_features() było wywołane?")

    velocity_df = features_df[norm_cols].diff().fillna(0.0)
    velocity_df.columns = [f"{c}_dt" for c in norm_cols]
    return velocity_df, list(velocity_df.columns)
