"""Auto-etykietowanie faz biegu na podstawie pozycji stóp.

Algorytm oparty na detekcji peaków (foot strikes) w sygnale max(heel_y, foot_index_y).
Dla każdego CSV z keypointami wyznacza fazę biegu per klatka:
LEFT_STANCE, RIGHT_STANCE, FLIGHT, DOUBLE_SUPPORT.
Dodaje kolumny phase_auto (surowa) i phase (po filtrze medianowym) do CSV.
"""
import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import find_peaks, medfilt

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Fazy biegu
PHASES = ("LEFT_STANCE", "RIGHT_STANCE", "FLIGHT", "DOUBLE_SUPPORT")
PHASE_TO_INT = {p: i for i, p in enumerate(PHASES)}
INT_TO_PHASE = {i: p for i, p in enumerate(PHASES)}


# ---------------------------------------------------------------------------
# Detekcja kierunku
# ---------------------------------------------------------------------------

def detect_facing_direction(df: pd.DataFrame) -> str:
    """Wykryj w którą stronę zwrócony jest biegacz (LEFT / RIGHT).

    Porównuje średnią pozycję X nosa ze środkiem bioder.
    """
    nose_x = df["NOSE_x"].mean()
    mid_hip_x = (df["LEFT_HIP_x"].mean() + df["RIGHT_HIP_x"].mean()) / 2
    direction = "RIGHT" if nose_x > mid_hip_x else "LEFT"
    log.info("Kierunek biegu: %s (NOSE_x=%.3f, mid_HIP_x=%.3f)",
             direction, nose_x, mid_hip_x)
    return direction


# ---------------------------------------------------------------------------
# Klasyfikacja faz — podejście peak-based
# ---------------------------------------------------------------------------

def _get_foot_signals(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Sygnał kontaktu per stopa: max(heel_y, foot_index_y).

    Obejmuje cały cykl kontaktu od heel strike do toe-off.
    """
    left = np.maximum(df["LEFT_HEEL_y"].values, df["LEFT_FOOT_INDEX_y"].values)
    right = np.maximum(df["RIGHT_HEEL_y"].values, df["RIGHT_FOOT_INDEX_y"].values)
    return left, right


def _detect_foot_strikes(
    foot_y: np.ndarray,
    fps: float,
    min_prominence: float = 0.03,
    max_cadence_per_foot: float = 150.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Wykryj momenty kontaktu stopy z podłożem (peaki w sygnale foot_y).

    Zwraca (indeksy_peaków, prominencje).
    """
    # Min odległość: przy max_cadence_per_foot kontaktów/min jednej stopy
    min_dist = max(3, int(fps * 60 / max_cadence_per_foot))
    peaks, props = find_peaks(foot_y, distance=min_dist, prominence=min_prominence)
    return peaks, props["prominences"]


def _enforce_alternation(
    l_peaks: np.ndarray, l_proms: np.ndarray,
    r_peaks: np.ndarray, r_proms: np.ndarray,
) -> list[tuple[int, str]]:
    """Scal peaki obu stóp i wymuś alternację L-R-L-R.

    Jeśli dwa te same z rzędu — zachowaj ten z wyższą prominence.
    Zwraca listę (frame, side) w kolejności chronologicznej.
    """
    events: list[tuple[int, str, float]] = []
    events.extend((f, "L", p) for f, p in zip(l_peaks, l_proms))
    events.extend((f, "R", p) for f, p in zip(r_peaks, r_proms))
    events.sort(key=lambda x: x[0])

    if not events:
        return []

    filtered = [events[0]]
    for ev in events[1:]:
        if ev[1] == filtered[-1][1]:
            # Ten sam typ z rzędu — zachowaj mocniejszy
            if ev[2] > filtered[-1][2]:
                filtered[-1] = ev
        else:
            filtered.append(ev)

    return [(f, s) for f, s, _ in filtered]


def _assign_phases_from_peaks(
    contacts: list[tuple[int, str]],
    left_foot_y: np.ndarray,
    right_foot_y: np.ndarray,
    n_frames: int,
    flight_fraction: float = 0.3,
) -> np.ndarray:
    """Przypisz fazy na podstawie wykrytych kontaktów.

    Dla każdej pary sąsiednich kontaktów:
    - Znajdź punkt min(max(L,R)) — centrum fazy lotu
    - Rozdziel klatki na STANCE (wokół peaka) i FLIGHT (wokół minimum)
    """
    nearest = np.maximum(left_foot_y, right_foot_y)
    phases = np.full(n_frames, "FLIGHT", dtype="U20")

    if len(contacts) < 2:
        log.warning("Za mało kontaktów (%d) — nie da się wyznaczyć faz", len(contacts))
        return phases

    # Wyznacz punkty przejścia (min nearest) między peakami
    transitions = []
    for i in range(len(contacts) - 1):
        f1 = contacts[i][0]
        f2 = contacts[i + 1][0]
        if f2 - f1 <= 2:
            transitions.append((f1 + f2) // 2)
        else:
            seg = nearest[f1 + 1:f2]
            transitions.append(f1 + 1 + int(np.argmin(seg)))

    # Przypisz fazy per region (od transition[i-1] do transition[i])
    for i, (frame, side) in enumerate(contacts):
        label = "LEFT_STANCE" if side == "L" else "RIGHT_STANCE"

        # Granice regionu
        region_start = 0 if i == 0 else transitions[i - 1]
        region_end = n_frames if i >= len(transitions) else transitions[i]

        region_len = region_end - region_start
        # Margines flight na brzegach regionu (min 1 klatka, proporcjonalny do rozmiaru)
        margin = max(1, int(region_len * flight_fraction / 2))

        for f in range(region_start, region_end):
            is_leading_flight = (i > 0) and (f < region_start + margin)
            is_trailing_flight = (i < len(contacts) - 1) and (f >= region_end - margin)

            if is_leading_flight or is_trailing_flight:
                phases[f] = "FLIGHT"
            else:
                phases[f] = label

    return phases


def classify_phases(
    df: pd.DataFrame,
    fps: float,
    min_prominence: float = 0.03,
    flight_fraction: float = 0.3,
) -> tuple[np.ndarray, dict]:
    """Klasyfikuj fazę biegu per klatka (peak-based).

    1. Wyznacz sygnał kontaktu per stopa: max(heel_y, foot_index_y)
    2. Wykryj peaki (foot strikes) per stopa
    3. Wymuś alternację L-R
    4. Przypisz STANCE wokół peaków, FLIGHT w przejściach

    Zwraca (tablica etykiet, dict diagnostyczny).
    """
    left_foot_y, right_foot_y = _get_foot_signals(df)
    n = len(df)

    l_peaks, l_proms = _detect_foot_strikes(left_foot_y, fps, min_prominence)
    r_peaks, r_proms = _detect_foot_strikes(right_foot_y, fps, min_prominence)
    log.info("Peaki: LEFT=%d, RIGHT=%d", len(l_peaks), len(r_peaks))

    contacts = _enforce_alternation(l_peaks, l_proms, r_peaks, r_proms)
    log.info("Kontakty po alternacji: %d (oczekiwane ~%d)",
             len(contacts), int(n / fps * 170 / 60))

    phases = _assign_phases_from_peaks(
        contacts, left_foot_y, right_foot_y, n, flight_fraction,
    )

    n_l = sum(1 for _, s in contacts if s == "L")
    n_r = sum(1 for _, s in contacts if s == "R")
    diag = {
        "left_contacts": n_l,
        "right_contacts": n_r,
        "total_contacts": len(contacts),
        "min_prominence": min_prominence,
        "flight_fraction": flight_fraction,
    }
    return phases, diag


# ---------------------------------------------------------------------------
# Filtr medianowy
# ---------------------------------------------------------------------------

def apply_median_filter(phases: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """Filtr medianowy na sekwencji etykiet — eliminuje migotanie (1-2 klatki)."""
    numeric = np.array([PHASE_TO_INT[p] for p in phases], dtype=np.float64)
    filtered = medfilt(numeric, kernel_size=kernel_size).astype(int)
    return np.array([INT_TO_PHASE[v] for v in filtered])


# ---------------------------------------------------------------------------
# Korekta L/R
# ---------------------------------------------------------------------------

def swap_left_right(phases: np.ndarray) -> np.ndarray:
    """Zamień LEFT_STANCE <-> RIGHT_STANCE (gdy biegacz zwrócony w lewo)."""
    swap_map = {
        "LEFT_STANCE": "RIGHT_STANCE",
        "RIGHT_STANCE": "LEFT_STANCE",
        "FLIGHT": "FLIGHT",
        "DOUBLE_SUPPORT": "DOUBLE_SUPPORT",
    }
    return np.array([swap_map[p] for p in phases])


# ---------------------------------------------------------------------------
# Diagnostyka
# ---------------------------------------------------------------------------

def compute_diagnostics(phases: np.ndarray, fps: float) -> dict:
    """Statystyki diagnostyczne do oceny jakości etykietowania."""
    n = len(phases)
    duration_s = n / fps if fps > 0 else 0

    # Rozkład faz
    unique, counts = np.unique(phases, return_counts=True)
    dist = {p: 0 for p in PHASES}
    for p, c in zip(unique, counts):
        dist[p] = int(c)

    # Przejścia i kadencja
    transitions = int(np.sum(phases[1:] != phases[:-1]))
    stance_entries = sum(
        1 for i in range(1, n)
        if phases[i] in ("LEFT_STANCE", "RIGHT_STANCE") and phases[i] != phases[i - 1]
    )
    cadence = (stance_entries / duration_s) * 60 if duration_s > 0 else 0

    # Bezpośrednie L↔R (bez FLIGHT)
    direct_lr = sum(
        1 for i in range(1, n)
        if (phases[i] == "LEFT_STANCE" and phases[i - 1] == "RIGHT_STANCE")
        or (phases[i] == "RIGHT_STANCE" and phases[i - 1] == "LEFT_STANCE")
    )

    # Segmenty per faza
    segment_durations: dict[str, list[float]] = {p: [] for p in PHASES}
    current_phase = phases[0]
    current_len = 1
    for i in range(1, n):
        if phases[i] == current_phase:
            current_len += 1
        else:
            segment_durations[current_phase].append(current_len / fps)
            current_phase = phases[i]
            current_len = 1
    segment_durations[current_phase].append(current_len / fps)

    seg_stats = {}
    for p in PHASES:
        durations = segment_durations[p]
        if durations:
            seg_stats[p] = {
                "count": len(durations),
                "mean_s": round(np.mean(durations), 4),
                "std_s": round(np.std(durations), 4),
                "min_s": round(np.min(durations), 4),
                "max_s": round(np.max(durations), 4),
            }

    return {
        "frames": n,
        "fps": fps,
        "duration_s": round(duration_s, 2),
        "phase_distribution": dist,
        "transitions": transitions,
        "direct_lr_transitions": direct_lr,
        "estimated_cadence_spm": round(cadence, 1),
        "segment_stats": seg_stats,
    }


def print_diagnostics(diag: dict, label: str = "") -> None:
    """Wypisuje diagnostykę w czytelnej formie."""
    prefix = f"[{label}] " if label else ""
    log.info("%sCzas: %.2fs, FPS: %.1f, klatek: %d",
             prefix, diag["duration_s"], diag["fps"], diag["frames"])

    dist = diag["phase_distribution"]
    total = diag["frames"]
    log.info("%sRozkład faz:", prefix)
    for p in PHASES:
        cnt = dist.get(p, 0)
        pct = 100 * cnt / total if total > 0 else 0
        log.info("  %-20s %4d klatek (%5.1f%%)", p, cnt, pct)

    log.info("%sKadencja: %.1f kroków/min, przejścia: %d, bezpośrednie L↔R: %d",
             prefix, diag["estimated_cadence_spm"], diag["transitions"],
             diag["direct_lr_transitions"])

    seg = diag.get("segment_stats", {})
    if seg:
        log.info("%sCzasy segmentów:", prefix)
        for p in PHASES:
            if p in seg:
                s = seg[p]
                log.info("  %-20s n=%d, mean=%.0fms (std=%.0fms), range=[%.0f, %.0f]ms",
                         p, s["count"], s["mean_s"] * 1000, s["std_s"] * 1000,
                         s["min_s"] * 1000, s["max_s"] * 1000)


# ---------------------------------------------------------------------------
# Pipeline etykietowania
# ---------------------------------------------------------------------------

def label_one_file(
    csv_path: Path,
    min_prominence: float = 0.03,
    flight_fraction: float = 0.4,
    median_kernel: int = 3,
    save: bool = True,
) -> pd.DataFrame:
    """Etykietuje fazy biegu w jednym pliku CSV z keypointami."""
    log.info("=" * 60)
    log.info("Przetwarzanie: %s", csv_path.name)
    df = pd.read_csv(csv_path)

    # Pomiń klatki bez detekcji
    if "pose_detected" in df.columns:
        no_pose = (df["pose_detected"] == 0).sum()
        if no_pose > 0:
            log.warning("%d klatek bez detekcji pozy", no_pose)

    # Kierunek biegu
    direction = detect_facing_direction(df)

    # FPS z timestampów
    if len(df) >= 2:
        dt = df["timestamp"].iloc[1] - df["timestamp"].iloc[0]
        fps = 1.0 / dt if dt > 0 else 30.0
    else:
        fps = 30.0
    log.info("FPS: %.2f", fps)

    # Klasyfikacja faz (surowa, peak-based)
    phases_raw, phase_diag = classify_phases(
        df, fps, min_prominence=min_prominence, flight_fraction=flight_fraction,
    )

    # Korekta kierunku
    if direction == "LEFT":
        log.info("Biegacz zwrócony w lewo — zamieniam LEFT/RIGHT")
        phases_raw = swap_left_right(phases_raw)

    # Diagnostyka surowej klasyfikacji
    log.info("--- Przed filtrem medianowym ---")
    diag_raw = compute_diagnostics(phases_raw, fps)
    print_diagnostics(diag_raw, "RAW")

    # Filtr medianowy
    phases_filtered = apply_median_filter(phases_raw, kernel_size=median_kernel)

    # Diagnostyka po filtrze
    log.info("--- Po filtrze medianowym (kernel=%d) ---", median_kernel)
    diag_filtered = compute_diagnostics(phases_filtered, fps)
    print_diagnostics(diag_filtered, "FILTERED")

    changed = int(np.sum(phases_raw != phases_filtered))
    log.info("Filtr zmienił %d/%d klatek (%.1f%%)",
             changed, len(df), 100 * changed / len(df))

    # Usuń stare kolumny jeśli istnieją (re-run)
    df = df.drop(columns=["phase_auto", "phase"], errors="ignore")

    # Dopisz kolumny
    df = pd.concat([
        df,
        pd.DataFrame({"phase_auto": phases_raw, "phase": phases_filtered}),
    ], axis=1)

    if save:
        df.to_csv(csv_path, index=False, encoding="utf-8")
        log.info("Zapisano: %s", csv_path.name)

    return df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auto-etykietowanie faz biegu na podstawie detekcji foot strikes."
    )
    parser.add_argument(
        "--keypoints-dir", default="data/keypoints",
        help="Katalog z CSV keypointów",
    )
    parser.add_argument(
        "--file", default=None,
        help="Ścieżka do pojedynczego CSV (domyślnie przetwarza cały katalog)",
    )
    parser.add_argument(
        "--min-prominence", type=float, default=0.03,
        help="Minimalna prominence peaka foot strike (domyślnie 0.03)",
    )
    parser.add_argument(
        "--flight-fraction", type=float, default=0.4,
        help="Frakcja interwału między peakami przeznaczona na FLIGHT (domyślnie 0.4)",
    )
    parser.add_argument(
        "--median-kernel", type=int, default=3,
        help="Rozmiar kernela filtra medianowego (domyślnie 3)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Nie zapisuj zmian — tylko diagnostyka",
    )
    args = parser.parse_args()

    if args.file:
        files = [Path(args.file)]
    else:
        kp_dir = Path(args.keypoints_dir)
        files = sorted(
            f for f in kp_dir.glob("*.csv")
            if not f.name.startswith("_")
        )

    log.info("Plików do etykietowania: %d", len(files))

    for csv_path in files:
        try:
            label_one_file(
                csv_path,
                min_prominence=args.min_prominence,
                flight_fraction=args.flight_fraction,
                median_kernel=args.median_kernel,
                save=not args.dry_run,
            )
        except Exception as e:
            log.error("Błąd przy %s: %s", csv_path.name, e, exc_info=True)


if __name__ == "__main__":
    main()
