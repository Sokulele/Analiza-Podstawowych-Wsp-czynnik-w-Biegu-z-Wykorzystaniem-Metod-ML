"""Wartości referencyjne współczynników biegu — synced z `docs/reference-values.md`.

Źródła: Novacheck 1998, Heiderscheit 2011, Souza 2016, Diaz 2019.

Jeśli zmienisz wartości tutaj, zaktualizuj też `docs/reference-values.md` (źródło prawdy
dla pracy magisterskiej). Format: każdy współczynnik ma listę zakresów (kategorii)
+ optional ostrzeżenia (warnings) dla wartości poza wszystkimi zakresami.

Funkcja `classify_value(value, key)` zwraca klasyfikację (label) + active warnings.

Konwencja:
- ranges są malejące lub rosnące w zależności od współczynnika
- Wartość poza wszystkimi range'ami otrzymuje "out_of_typical"
- warnings_low / warnings_high są aplikowane gdy value < min_pierwszego_range / > max_ostatniego_range
- warnings (lista) są aplikowane na wartości spełniające condition (op + threshold)
"""
from __future__ import annotations

from dataclasses import dataclass


# Główny słownik referencji
REFERENCE_VALUES: dict = {
    "cadence_spm": {
        "ranges": [
            {"label": "rekreacyjny", "min": 150, "max": 170},
            {"label": "zaawansowany", "min": 170, "max": 185},
            {"label": "elita", "min": 185, "max": 200},
        ],
        "warning_low": "Kadencja < 150 spm: bardzo niska, może oznaczać overstriding / chód",
        "recommendation": "celuj w 170-180 spm (zmniejsza obciążenie stawów)",
        "unit": "spm",
        "direction": "higher_better_to_limit",
    },
    "gct_ms": {
        "ranges": [
            {"label": "elita", "min": 150, "max": 200},
            {"label": "szybki bieg", "min": 200, "max": 220},
            {"label": "rekreacyjny", "min": 220, "max": 280},
            {"label": "jogging (wolny)", "min": 280, "max": 350},
        ],
        "warning_low": "GCT < 150 ms: nietypowo krótki, sprawdź dokładność predykcji",
        "warning_high": "GCT > 350 ms: sugeruje wolny jogging lub chód",
        "recommendation": "krótszy GCT = lepsza ekonomia (do pewnej granicy)",
        "unit": "ms",
        "direction": "lower_better_to_limit",
    },
    "flight_ms": {
        "ranges": [
            {"label": "typowy bieg", "min": 80, "max": 150},
        ],
        "warning_low": "Flight time < 80 ms: ledwo bieg, blisko chodu",
        "warning_high": "Flight time > 150 ms: bardzo długa faza lotu, zwykle sprint",
        "unit": "ms",
    },
    "duty_factor": {
        "ranges": [
            {"label": "sprint", "min": 0.22, "max": 0.30},
            {"label": "rekreacyjny", "min": 0.35, "max": 0.45},
        ],
        "warning_high": "Duty factor >= 0.5: technicznie chód, nie bieg",
        "unit": "",
        "direction": "lower_better",
    },
    "knee_angle_initial_contact_deg": {
        "ranges": [
            {"label": "prawidłowy", "min": 160, "max": 175},
        ],
        "warnings": [
            {"op": ">", "threshold": 175, "msg": "overstriding (kolano zbyt wyprostowane), ryzyko kontuzji"},
            {"op": "<", "threshold": 155, "msg": "'siedzący' bieg (kolano zbyt ugięte), strata energii"},
        ],
        "unit": "deg",
    },
    "torso_lean_deg": {
        "ranges": [
            {"label": "prawidłowy", "min": 5, "max": 15},
        ],
        "warnings": [
            {"op": "<", "threshold": 5, "msg": "tułów zbyt pionowy, brak wykorzystania grawitacji"},
            {"op": ">", "threshold": 20, "msg": "tułów zbyt pochylony, ryzyko obciążenia kręgosłupa"},
        ],
        "unit": "deg",
    },
    "vertical_oscillation_cm": {
        "ranges": [
            {"label": "dobry biegacz", "min": 6, "max": 8},
            {"label": "rekreacyjny", "min": 8, "max": 12},
        ],
        "warning_high": "Vertical oscillation > 12 cm: marnowanie energii na ruch pionowy",
        "unit": "cm",
        "direction": "lower_better",
    },
    "vertical_oscillation_per_torso": {
        "info": "Wartość znormalizowana długością tułowia (bezwymiarowa). "
                "Dla typowego tułowia ~50 cm: 0.12-0.16 = ~6-8 cm = dobry biegacz, "
                "0.16-0.24 = ~8-12 cm = rekreacyjny, >0.24 = >12 cm = marnowanie energii.",
        "ranges": [
            {"label": "dobry biegacz", "min": 0.12, "max": 0.16},
            {"label": "rekreacyjny", "min": 0.16, "max": 0.24},
        ],
        "warning_low": "Bardzo niska oscylacja (< 0.12 torso): możliwy szum keypointów",
        "warning_high": "Oscylacja > 0.24 torso: marnowanie energii",
        "unit": "(per torso)",
    },
    "symmetry_si_pct": {
        "ranges": [
            {"label": "norma", "min": 0, "max": 5},
            {"label": "wymaga uwagi", "min": 5, "max": 10},
            {"label": "potencjalny problem", "min": 10, "max": 100},
        ],
        "unit": "%",
        "direction": "lower_better",
    },
    "foot_strike_distribution": {
        "info": "Rearfoot ~75%, midfoot ~20%, forefoot ~5% biegaczy rekreacyjnych. "
                "Brak rekomendacji 'najlepszego' — ważniejsze jest overstriding.",
        "no_classification": True,
    },
}


@dataclass
class Classification:
    """Wynik klasyfikacji jednej wartości."""
    value: float | None
    label: str  # "rekreacyjny", "norma", "out_of_typical", "—" (gdy brak)
    warnings: list[str]
    unit: str

    def status_emoji(self) -> str:
        """Emoji do raportu MD — heurystyka oparta na label + warnings."""
        # Etykiety jednoznacznie negatywne (z ranges, np. SI 10-100%)
        bad_labels = {"potencjalny problem"}
        # Etykiety wymagające uwagi
        warn_labels = {"wymaga uwagi", "asymetria łagodna"}
        # Etykiety w pełni pozytywne — pierwsza w listach ranges dla "lower_better"
        # lub "prawidłowy" itp. Wszystkie nie-warn nie-bad traktujemy jako OK
        if self.label in bad_labels:
            return "🔴"
        if self.label in warn_labels:
            return "🟡"
        if self.label == "out_of_typical":
            # "out_of_typical" + warning z "ryzyko"/"problem" → 🔴
            critical_terms = ("ryzyko", "problem", "chód", "marnowanie", "obciążenie")
            if any(any(t in w.lower() for t in critical_terms) for w in self.warnings):
                return "🔴"
            return "🟡"
        if self.label == "—":
            return "—"
        # Pozytywne klasyfikacje (norma, prawidłowy, rekreacyjny, dobry biegacz, ...)
        # ale jeśli mają warnings — 🟡 (sygnał na uwagę mimo bycia w zakresie)
        if self.warnings:
            return "🟡"
        return "✅"


def classify_value(value: float | None, key: str) -> Classification:
    """Klasyfikuj wartość względem zakresów referencyjnych.

    Zwraca `Classification(value, label, warnings, unit)`.
    """
    ref = REFERENCE_VALUES.get(key)
    if ref is None:
        return Classification(value, "—", [], "")

    unit = ref.get("unit", "")

    if value is None or ref.get("no_classification"):
        return Classification(value, "—", [], unit)

    label = "out_of_typical"
    warnings_active: list[str] = []

    ranges = ref.get("ranges", [])
    for r in ranges:
        if r["min"] <= value <= r["max"]:
            label = r["label"]
            break

    # Single-string warnings (low/high)
    if ranges:
        all_min = min(r["min"] for r in ranges)
        all_max = max(r["max"] for r in ranges)
        if value < all_min and "warning_low" in ref:
            warnings_active.append(ref["warning_low"])
        elif value > all_max and "warning_high" in ref:
            warnings_active.append(ref["warning_high"])

    # Custom warnings list (op + threshold)
    for w in ref.get("warnings", []):
        op = w["op"]
        threshold = w["threshold"]
        if op == ">" and value > threshold:
            warnings_active.append(w["msg"])
        elif op == ">=" and value >= threshold:
            warnings_active.append(w["msg"])
        elif op == "<" and value < threshold:
            warnings_active.append(w["msg"])
        elif op == "<=" and value <= threshold:
            warnings_active.append(w["msg"])

    return Classification(value, label, warnings_active, unit)


def get_recommendation(key: str) -> str | None:
    """Ogólna rekomendacja dla danego współczynnika (do pokazania pod tabelą)."""
    ref = REFERENCE_VALUES.get(key, {})
    return ref.get("recommendation") or ref.get("info")
