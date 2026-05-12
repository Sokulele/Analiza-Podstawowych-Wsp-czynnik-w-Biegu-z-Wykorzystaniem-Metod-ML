"""Silnik reguł rekomendacji biegowych — Etap 7.

Reguły są **kodowane ręcznie na podstawie literatury biomechanicznej** (NIE uczone z danych)
— zgodnie z CLAUDE.md (sekcja "Rekomendacje"). Operują na JSON-ach generowanych przez
`src/coefficients/analyze.py` (temporal / spatial / symmetry / meta) i zwracają listę
obiektów `Recommendation` ze severity + citation.

## Źródła literaturowe

- **Heiderscheit, B.C. et al. (2011)** — "Effects of step rate manipulation on joint
  mechanics during running." *Med Sci Sports Exerc 43(2), 296–302*. Zwiększenie kadencji
  o 5–10% obniża obciążenia stawów.
- **Novacheck, T.F. (1998)** — "The biomechanics of running." *Gait & Posture 7(1), 77–95*.
  Pochylenie tułowia, kąt kolana przy kontakcie, overstriding.
- **Souza, R.B. (2016)** — "An Evidence-Based Videotaped Running Biomechanics Analysis."
  *Phys Med Rehabil Clin N Am 27(1), 217–236*. GCT, duty factor, foot strike.
- **Diaz, J.J. et al. (2019)** — IMU + pose estimation w analizie biegu. Vertical
  oscillation jako wskaźnik ekonomii ruchu.
- **Robinson, R.O. et al. (1987)** — Robinson's Symmetry Index: SI = 200·|L−R|/(L+R).
  Progi 5% / 10%.
- **Daoud, A.I. et al. (2012)** — "Foot strike and injury rates in endurance runners."
  *Med Sci Sports Exerc 44(7), 1325–1334*. Częstość heel strike vs forefoot.

## Severity

- `critical` — wymaga interwencji (potencjalne ryzyko kontuzji lub silny artefakt predykcji)
- `warning` — wartość poza zalecanym zakresem, ale nie krytyczna
- `watch` — w zakresie akceptowalnym, ale monitoruj
- `info` — informacja pozytywna lub neutralna

## Użycie

    from recommendations.rules import generate_recommendations
    result = generate_recommendations(meta, temporal, spatial, symmetry)
    # result = {"recommendations": [...], "summary": {...}}
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

Severity = Literal["critical", "warning", "watch", "info"]

_SEVERITY_ORDER: dict[str, int] = {"critical": 0, "warning": 1, "watch": 2, "info": 3}
_SEVERITY_EMOJI: dict[str, str] = {
    "critical": "🔴",
    "warning": "🟠",
    "watch": "🟡",
    "info": "ℹ️",
}


@dataclass
class Recommendation:
    """Pojedyncza rekomendacja wygenerowana przez regułę z literatury."""

    rule_id: str
    severity: Severity
    category: str  # "kadencja", "GCT", "tułów", "kolano@kontakt", "vert_osc", "symetria", "foot_strike", "duty_factor", "jakość_predykcji"
    title: str
    message: str  # pełna treść po polsku
    citation: str  # autor + rok
    detail: str = ""  # opcjonalnie: konkretne liczby (np. "kadencja 144 spm, cel 170-180")
    suggestion: str = ""  # konkretne działanie ("zwiększ kadencję o ~8 spm")

    def emoji(self) -> str:
        return _SEVERITY_EMOJI.get(self.severity, "•")


# -----------------------------------------------------------------------------
# Reguły per temat
# -----------------------------------------------------------------------------

def check_cadence(temporal: dict) -> list[Recommendation]:
    """Reguły na kadencji (Heiderscheit 2011)."""
    out: list[Recommendation] = []
    cad = temporal.get("cadence", {}).get("cadence_spm")
    if cad is None:
        return out

    if cad < 150:
        out.append(Recommendation(
            rule_id="cadence_very_low",
            severity="critical",
            category="kadencja",
            title="Kadencja bardzo niska",
            message=(
                "Kadencja poniżej 150 spm odbiega od typowego zakresu biegu (150–185 spm). "
                "Może oznaczać overstriding lub przejście w chód. Sprawdź, czy materiał wideo "
                "rzeczywiście pokazuje bieg ciągły."
            ),
            citation="Heiderscheit et al. 2011; Novacheck 1998",
            detail=f"kadencja zmierzona: {cad:.0f} spm, cel: 170–180 spm",
            suggestion="Skróć krok i zwiększ częstość kontaktów (~+15–20 spm), tak aby zbliżyć się do 170 spm.",
        ))
    elif cad < 160:
        out.append(Recommendation(
            rule_id="cadence_low",
            severity="warning",
            category="kadencja",
            title="Niska kadencja — ryzyko overstridingu",
            message=(
                "Kadencja w zakresie 150–160 spm to często symptom za długiego kroku (overstriding), "
                "który zwiększa siły uderzeniowe w kolanie i biodrze. Heiderscheit i wsp. wykazali, "
                "że zwiększenie kadencji o 5–10% wyraźnie obniża obciążenie stawów."
            ),
            citation="Heiderscheit et al. 2011",
            detail=f"kadencja zmierzona: {cad:.0f} spm, zalecany cel: 170–180 spm",
            suggestion=f"Spróbuj zwiększyć kadencję o ~{max(5, round(cad * 0.05)):.0f}–{round(cad * 0.10):.0f} spm "
                       f"(do ~{cad + cad * 0.075:.0f} spm). Pomocna metoda: bieg z metronomem.",
        ))
    elif cad < 170:
        out.append(Recommendation(
            rule_id="cadence_recreational",
            severity="watch",
            category="kadencja",
            title="Kadencja rekreacyjna — możliwość poprawy",
            message=(
                "Kadencja w zakresie 160–170 spm jest typowa dla biegaczy rekreacyjnych. "
                "Stopniowe podniesienie do 170–180 spm może zmniejszyć obciążenie stawów."
            ),
            citation="Heiderscheit et al. 2011",
            detail=f"kadencja: {cad:.0f} spm",
            suggestion="Cel długoterminowy: 170–180 spm. Wprowadzaj zmianę stopniowo (~5%/tydzień).",
        ))
    elif cad <= 185:
        out.append(Recommendation(
            rule_id="cadence_optimal",
            severity="info",
            category="kadencja",
            title="Kadencja w zalecanym zakresie",
            message="Kadencja mieści się w zakresie zalecanym dla zaawansowanych biegaczy (170–185 spm).",
            citation="Heiderscheit et al. 2011",
            detail=f"kadencja: {cad:.0f} spm",
        ))
    elif cad <= 200:
        out.append(Recommendation(
            rule_id="cadence_elite",
            severity="info",
            category="kadencja",
            title="Kadencja na poziomie elity",
            message="Kadencja w zakresie 185–200 spm to typowy poziom biegaczy zawodowych / sprinterów.",
            citation="Novacheck 1998",
            detail=f"kadencja: {cad:.0f} spm",
        ))
    else:
        out.append(Recommendation(
            rule_id="cadence_extreme",
            severity="watch",
            category="kadencja",
            title="Kadencja bardzo wysoka",
            message=(
                "Kadencja >200 spm jest nietypowa nawet dla sprinterów na krótkich dystansach. "
                "Zweryfikuj, czy nie jest to artefakt predykcji (np. nadmierne segmentowanie faz)."
            ),
            citation="Novacheck 1998",
            detail=f"kadencja: {cad:.0f} spm",
        ))
    return out


def check_gct(temporal: dict) -> list[Recommendation]:
    """Reguły na czasie kontaktu z podłożem (Souza 2016, Heiderscheit 2011).

    Łączy też regułę overstriding (kadencja < 160 + GCT > 270 ms).
    """
    out: list[Recommendation] = []
    gct_l = temporal.get("phase_durations", {}).get("gct_left", {}).get("mean_ms")
    gct_r = temporal.get("phase_durations", {}).get("gct_right", {}).get("mean_ms")
    cad = temporal.get("cadence", {}).get("cadence_spm")

    for side, gct in (("lewa", gct_l), ("prawa", gct_r)):
        if gct is None:
            continue
        if gct > 350:
            out.append(Recommendation(
                rule_id=f"gct_{side}_too_long",
                severity="critical",
                category="GCT",
                title=f"GCT {side}: bardzo długi czas kontaktu",
                message=(
                    f"GCT {side} > 350 ms sugeruje jogging na pograniczu chodu albo błąd predykcji fazy. "
                    "Długi GCT silnie zwiększa obciążenie stawów."
                ),
                citation="Souza 2016",
                detail=f"GCT {side}: {gct:.0f} ms (typowy bieg rekreacyjny: 220–280 ms)",
                suggestion="Zwiększ kadencję — krótszy krok skraca czas kontaktu z podłożem.",
            ))
        elif gct > 280:
            out.append(Recommendation(
                rule_id=f"gct_{side}_long",
                severity="warning",
                category="GCT",
                title=f"GCT {side}: przedłużony",
                message=(
                    f"GCT {side} w zakresie 280–350 ms wskazuje na wolne tempo lub długi krok. "
                    "U biegaczy rekreacyjnych zalecane 220–280 ms — krótszy GCT poprawia ekonomię biegu."
                ),
                citation="Souza 2016; Heiderscheit et al. 2011",
                detail=f"GCT {side}: {gct:.0f} ms",
                suggestion="Spróbuj zwiększyć kadencję o ~5–10% — zwykle skraca GCT bez wysiłku.",
            ))
        elif gct < 150:
            out.append(Recommendation(
                rule_id=f"gct_{side}_very_short",
                severity="watch",
                category="GCT",
                title=f"GCT {side}: nietypowo krótki",
                message=(
                    f"GCT {side} < 150 ms typowy dla sprinterów elity. Dla biegu rekreacyjnego "
                    "to wartość poza typowym zakresem — może być artefaktem predykcji fazy (model "
                    "może mylić L/R lub fragmentaryzować STANCE)."
                ),
                citation="Souza 2016",
                detail=f"GCT {side}: {gct:.0f} ms",
                suggestion="Zweryfikuj wzrokowo kilka cykli na materiale wideo.",
            ))

    # Reguła łączona: overstriding — kadencja niska + GCT długi
    if cad is not None and gct_l is not None and gct_r is not None:
        gct_mean = (gct_l + gct_r) / 2
        if cad < 160 and gct_mean > 270:
            out.append(Recommendation(
                rule_id="overstriding_combo",
                severity="warning",
                category="GCT",
                title="Sygnał overstriding (niska kadencja + długi GCT)",
                message=(
                    "Połączenie kadencji < 160 spm i średniego GCT > 270 ms jest klasycznym wzorcem "
                    "overstridingu — stopa ląduje znacznie przed środkiem ciężkości, co zwiększa siły "
                    "hamowania i obciążenie kolan."
                ),
                citation="Heiderscheit et al. 2011; Novacheck 1998",
                detail=f"kadencja {cad:.0f} spm, GCT średni {gct_mean:.0f} ms",
                suggestion="Zwiększ kadencję o 5–10% — to najczęstszy zalecany sposób korekcji overstridingu.",
            ))

    return out


def check_duty_factor(temporal: dict) -> list[Recommendation]:
    """Reguły na duty factor (Souza 2016)."""
    out: list[Recommendation] = []
    df = temporal.get("duty_factor", {})
    df_l = df.get("duty_factor_left")
    df_r = df.get("duty_factor_right")

    for side, val in (("lewa", df_l), ("prawa", df_r)):
        if val is None:
            continue
        if val >= 0.5:
            out.append(Recommendation(
                rule_id=f"duty_{side}_walk",
                severity="critical",
                category="duty_factor",
                title=f"Duty factor {side}: technicznie chód",
                message=(
                    f"Duty factor {side} ≥ 0.5 oznacza, że stopa jest w kontakcie z podłożem przez ponad "
                    "połowę cyklu — biomechanicznie to chód, nie bieg. Sprawdź materiał wideo lub predykcję fazy."
                ),
                citation="Souza 2016",
                detail=f"DF {side}: {val:.3f} (bieg: <0.5, rekreacyjny: 0.35–0.45)",
            ))
        elif val > 0.45:
            out.append(Recommendation(
                rule_id=f"duty_{side}_high",
                severity="warning",
                category="duty_factor",
                title=f"Duty factor {side}: wysoki",
                message=(
                    f"DF {side} w zakresie 0.45–0.5 sygnalizuje długi kontakt względem cyklu — "
                    "lżejszy, częstszy krok zwykle poprawia ekonomię."
                ),
                citation="Souza 2016",
                detail=f"DF {side}: {val:.3f}",
                suggestion="Zwiększ kadencję, by skrócić względny udział fazy kontaktu.",
            ))
        elif val < 0.22:
            out.append(Recommendation(
                rule_id=f"duty_{side}_sprint",
                severity="watch",
                category="duty_factor",
                title=f"Duty factor {side}: bardzo niski",
                message=(
                    f"DF {side} < 0.22 typowy dla sprintów na pełnej prędkości. Dla biegu rekreacyjnego "
                    "to wartość poza typowym zakresem — może być artefaktem predykcji."
                ),
                citation="Souza 2016",
                detail=f"DF {side}: {val:.3f}",
            ))

    return out


def check_flight(temporal: dict) -> list[Recommendation]:
    """Reguła na czas lotu — sanity check (czy w ogóle mamy bieg)."""
    out: list[Recommendation] = []
    fl = temporal.get("phase_durations", {}).get("flight", {}).get("mean_ms")
    if fl is None:
        return out
    if fl < 30:
        out.append(Recommendation(
            rule_id="flight_almost_walk",
            severity="warning",
            category="GCT",  # bo bezpośrednio związane z fazami
            title="Bardzo krótka faza lotu — granica chodu",
            message=(
                "Średni czas lotu < 30 ms sugeruje, że ujęcie zawiera fragment chodu albo predykcja fazy "
                "FLIGHT jest fragmentaryczna."
            ),
            citation="Novacheck 1998",
            detail=f"flight: {fl:.0f} ms (typowy bieg: 80–150 ms)",
        ))
    return out


def check_torso_lean(spatial: dict) -> list[Recommendation]:
    """Reguły na pochylenie tułowia (Novacheck 1998)."""
    out: list[Recommendation] = []
    torso = spatial.get("torso_lean", {}).get("overall", {}).get("mean")
    if torso is None:
        return out

    if torso < 5:
        out.append(Recommendation(
            rule_id="torso_too_vertical",
            severity="warning",
            category="tułów",
            title="Tułów zbyt pionowy",
            message=(
                "Pochylenie tułowia < 5° (lub ujemne) oznacza brak wykorzystania grawitacji do napędu. "
                "Lekkie pochylenie z kostek (5–15°) wykorzystuje siłę ciężkości i obniża obciążenie nóg. "
                "UWAGA: wartość ta bywa zaniżona przez ograniczenia MediaPipe 2D — zweryfikuj wzrokowo."
            ),
            citation="Novacheck 1998",
            detail=f"pochylenie tułowia: {torso:.1f}° (cel: 5–15°)",
            suggestion="Ćwicz pochylenie 'z kostek, nie z bioder' (forward lean from ankles).",
        ))
    elif torso <= 15:
        out.append(Recommendation(
            rule_id="torso_optimal",
            severity="info",
            category="tułów",
            title="Pochylenie tułowia prawidłowe",
            message="Pochylenie tułowia w zakresie 5–15° to optymalne wykorzystanie grawitacji w biegu.",
            citation="Novacheck 1998",
            detail=f"pochylenie: {torso:.1f}°",
        ))
    elif torso <= 20:
        out.append(Recommendation(
            rule_id="torso_moderate_lean",
            severity="watch",
            category="tułów",
            title="Tułów wyraźnie pochylony",
            message=(
                "Pochylenie 15–20° to nadal akceptowalny zakres, ale długotrwałe utrzymywanie zwiększa "
                "obciążenie odcinka lędźwiowego kręgosłupa. Monitoruj zmęczenie pleców po długich biegach."
            ),
            citation="Novacheck 1998",
            detail=f"pochylenie: {torso:.1f}°",
        ))
    else:
        out.append(Recommendation(
            rule_id="torso_too_lean",
            severity="critical",
            category="tułów",
            title="Tułów zbyt pochylony",
            message=(
                "Pochylenie > 20° silnie obciąża dolny odcinek kręgosłupa i mięśnie pleców. "
                "Może też wskazywać na słabość mięśni core (głębokich stabilizatorów)."
            ),
            citation="Novacheck 1998",
            detail=f"pochylenie: {torso:.1f}°",
            suggestion="Wzmocnij core (plank, dead bug). Skonsultuj postawę z trenerem.",
        ))
    return out


def check_knee_at_contact(spatial: dict) -> list[Recommendation]:
    """Reguły na kąt kolana w initial contact (Heiderscheit 2011, Novacheck 1998)."""
    out: list[Recommendation] = []
    kc = spatial.get("knee_angle_at_contact", {})
    for side_key, side_pl in (("left_knee", "lewa"), ("right_knee", "prawa")):
        v = kc.get(side_key, {}).get("mean")
        if v is None:
            continue
        if v > 175:
            out.append(Recommendation(
                rule_id=f"knee_{side_pl}_overstriding",
                severity="critical",
                category="kolano@kontakt",
                title=f"Kolano {side_pl} przy kontakcie: zbyt wyprostowane (overstriding)",
                message=(
                    f"Kąt kolana > 175° w momencie kontaktu z podłożem oznacza, że stopa ląduje znacznie "
                    "przed środkiem ciężkości. To klasyczny wzorzec overstridingu — duże siły hamowania, "
                    "wysokie ryzyko kontuzji kolana (PFPS, IT band syndrome)."
                ),
                citation="Heiderscheit et al. 2011; Novacheck 1998",
                detail=f"kąt kolana {side_pl}: {v:.1f}° (prawidłowy zakres: 160–175°)",
                suggestion="Zwiększ kadencję o 5–10% — stopa będzie lądować bliżej środka ciężkości.",
            ))
        elif v < 155:
            out.append(Recommendation(
                rule_id=f"knee_{side_pl}_sitting",
                severity="watch",
                category="kolano@kontakt",
                title=f"Kolano {side_pl} przy kontakcie: zbyt ugięte ('siedzący' bieg)",
                message=(
                    f"Kąt kolana < 155° przy kontakcie wskazuje na 'siedzący' wzorzec biegu — "
                    "więcej pracy mięśni przy każdym kroku, mniejsze wykorzystanie energii elastycznej ścięgien. "
                    "UWAGA: bardzo niskie wartości (<100°) zwykle oznaczają błąd predykcji klatki kontaktu."
                ),
                citation="Novacheck 1998",
                detail=f"kąt kolana {side_pl}: {v:.1f}°",
            ))
        elif 160 <= v <= 175:
            out.append(Recommendation(
                rule_id=f"knee_{side_pl}_optimal",
                severity="info",
                category="kolano@kontakt",
                title=f"Kolano {side_pl} przy kontakcie: prawidłowe",
                message="Kąt kolana 160–175° w momencie kontaktu to optymalny zakres — lekko ugięte kolano absorbuje siłę uderzenia.",
                citation="Heiderscheit et al. 2011",
                detail=f"kąt kolana {side_pl}: {v:.1f}°",
            ))
    return out


def check_vertical_oscillation(spatial: dict) -> list[Recommendation]:
    """Reguły na vertical oscillation (Diaz 2019, Novacheck 1998).

    Używamy `vertical_oscillation_per_torso` (bezwymiarowa, niezależna od kalibracji piksel→cm).
    """
    out: list[Recommendation] = []
    vo = spatial.get("vertical_oscillation", {}).get("vertical_oscillation_per_torso", {}).get("mean")
    if vo is None:
        return out

    if vo > 0.24:
        out.append(Recommendation(
            rule_id="vert_osc_high",
            severity="warning",
            category="vert_osc",
            title="Wysoka oscylacja pionowa — marnowanie energii",
            message=(
                "Vertical oscillation > 0.24 długości tułowia (≈ >12 cm) oznacza nadmierny ruch w górę-dół. "
                "Energia idzie w 'podskakiwanie' zamiast w ruch poziomy, co obniża ekonomię biegu."
            ),
            citation="Diaz et al. 2019",
            detail=f"vert osc / torso: {vo:.3f} (cel: 0.12–0.16)",
            suggestion="Skup się na płynnym ruchu do przodu i wyższej kadencji — to zwykle redukuje pionowe skoki.",
        ))
    elif vo >= 0.16:
        out.append(Recommendation(
            rule_id="vert_osc_recreational",
            severity="watch",
            category="vert_osc",
            title="Oscylacja pionowa — poziom rekreacyjny",
            message=(
                "Oscylacja w zakresie 0.16–0.24 torso (≈ 8–12 cm) jest typowa dla rekreacyjnych biegaczy. "
                "Stopniowe obniżenie poprawi ekonomię biegu."
            ),
            citation="Diaz et al. 2019",
            detail=f"vert osc / torso: {vo:.3f}",
        ))
    elif vo >= 0.12:
        out.append(Recommendation(
            rule_id="vert_osc_good",
            severity="info",
            category="vert_osc",
            title="Oscylacja pionowa: ekonomiczny zakres",
            message="Oscylacja 0.12–0.16 torso (≈ 6–8 cm) to wartość typowa dla dobrych biegaczy.",
            citation="Diaz et al. 2019",
            detail=f"vert osc / torso: {vo:.3f}",
        ))
    else:
        out.append(Recommendation(
            rule_id="vert_osc_low",
            severity="watch",
            category="vert_osc",
            title="Bardzo niska oscylacja pionowa",
            message=(
                "Oscylacja < 0.12 torso jest nietypowa — może być wynikiem szumu keypointów MediaPipe "
                "(brak czubka głowy, biodro zasłonięte) lub bardzo płaskiego, krótkiego kroku."
            ),
            citation="Diaz et al. 2019",
            detail=f"vert osc / torso: {vo:.3f}",
        ))
    return out


def check_symmetry(symmetry: dict) -> list[Recommendation]:
    """Reguły na symetrię L/P (Robinson 1987).

    Stosujemy SI = 200·|L−R|/(L+R) z progami: <5% norma, 5–10% uwaga, >10% problem.
    Pomijamy metryki gdzie consistent=true (foot strike) lub brak danych.
    """
    out: list[Recommendation] = []

    metric_labels = {
        "gct": "GCT (czas kontaktu)",
        "cycle_time": "czas cyklu",
        "duty_factor": "duty factor",
        "knee_angle_stance": "kąt kolana w fazie stance",
        "ankle_angle_stance": "kąt kostki w fazie stance",
    }

    high_si: list[tuple[str, float]] = []  # (label, si) gdy SI > 10
    medium_si: list[tuple[str, float]] = []  # 5–10

    for key, label in metric_labels.items():
        entry = symmetry.get(key)
        if not entry:
            continue
        si = entry.get("symmetry_index_pct")
        if si is None:
            continue
        if si > 10:
            high_si.append((label, si))
        elif si >= 5:
            medium_si.append((label, si))

    if high_si:
        detail = "; ".join(f"{lbl} SI={si:.1f}%" for lbl, si in high_si)
        out.append(Recommendation(
            rule_id="symmetry_significant",
            severity="warning",
            category="symetria",
            title="Asymetria L/P powyżej 10% — rozważ konsultację",
            message=(
                "Wskaźnik symetrii Robinsona (SI = 200·|L−R|/(L+R)) powyżej 10% literatura traktuje "
                "jako sygnał potencjalnego dysbalansu mięśniowego lub kompensacji po przebytej kontuzji. "
                "UWAGA: część asymetrii w danych monocularnych 2D może być artefaktem perspektywy "
                "(strona bliżej kamery wydaje się ruszać 'większą amplitudą')."
            ),
            citation="Robinson et al. 1987; Souza 2016",
            detail=detail,
            suggestion="Jeżeli asymetria utrzymuje się na innych nagraniach, konsultacja z fizjoterapeutą.",
        ))

    if medium_si:
        detail = "; ".join(f"{lbl} SI={si:.1f}%" for lbl, si in medium_si)
        out.append(Recommendation(
            rule_id="symmetry_mild",
            severity="watch",
            category="symetria",
            title="Łagodna asymetria L/P (5–10%)",
            message=(
                "Wskaźnik symetrii Robinsona 5–10% to wartość 'do monitorowania' — drobne różnice między nogami "
                "są powszechne u rekreacyjnych biegaczy, ale warto obserwować trend w czasie."
            ),
            citation="Robinson et al. 1987",
            detail=detail,
        ))

    if not high_si and not medium_si and symmetry:
        out.append(Recommendation(
            rule_id="symmetry_healthy",
            severity="info",
            category="symetria",
            title="Symetria L/P w normie",
            message="Wszystkie wskaźniki symetrii < 5% — różnice między stronami są nieistotne.",
            citation="Robinson et al. 1987",
        ))

    return out


def check_foot_strike(spatial: dict, symmetry: dict) -> list[Recommendation]:
    """Reguły na foot strike pattern (Daoud 2012, Souza 2016).

    Literatura nie wskazuje jednoznacznie 'najlepszego' wzorca — najważniejsza
    jest spójność L/P i brak overstridingu (już sprawdzonego w check_knee_at_contact).
    """
    out: list[Recommendation] = []
    fs_sym = symmetry.get("foot_strike", {})
    if not fs_sym:
        return out

    left = fs_sym.get("left_dominant")
    right = fs_sym.get("right_dominant")
    consistent = fs_sym.get("consistent", False)

    if left and right and not consistent:
        out.append(Recommendation(
            rule_id="foot_strike_inconsistent",
            severity="warning",
            category="foot_strike",
            title=f"Różne wzorce lądowania L/P: {left} vs {right}",
            message=(
                f"Lewa stopa ląduje wzorcem '{left}', prawa wzorcem '{right}'. "
                "Różny wzorzec L/P sugeruje kompensację (np. po dawnej kontuzji), choć może też być "
                "artefaktem aspect ratio lub szumu keypointów stóp w MediaPipe."
            ),
            citation="Daoud et al. 2012; Souza 2016",
            detail=f"L: {left}, P: {right}",
            suggestion="Sprawdź wzrokowo kilka klatek initial contact. Jeśli wzorzec rzeczywisty, "
                       "warto skonsultować ze specjalistą.",
        ))
    elif left and right and consistent and left == right:
        out.append(Recommendation(
            rule_id="foot_strike_consistent",
            severity="info",
            category="foot_strike",
            title=f"Spójny wzorzec lądowania ({left})",
            message=(
                f"Obie stopy lądują tym samym wzorcem ({left}). Literatura nie wskazuje jednoznacznie "
                "'najlepszego' wzorca foot strike u dorosłych biegaczy — istotniejsza jest stabilność "
                "wzorca i brak overstridingu."
            ),
            citation="Daoud et al. 2012",
            detail=f"L=P={left}",
        ))
    return out


def check_data_quality(meta: dict, temporal: dict, symmetry: dict) -> list[Recommendation]:
    """Reguły walidacji jakości predykcji — wstawiane jako pierwsze ostrzeżenia.

    Trzy proxy 'low quality predictions' (z notatki 2026-05-09-iteracja1-test-set.md):
    - avg_confidence < 0.85
    - asymetria liczby kroków L/R > 20%
    - max SI > 30%
    """
    out: list[Recommendation] = []

    avg_conf = meta.get("avg_confidence") if meta else None
    cad = temporal.get("cadence", {})
    n_left = cad.get("n_steps_left")
    n_right = cad.get("n_steps_right")
    max_si = symmetry.get("overall", {}).get("max_si_pct")

    # Confidence < 0.85
    if avg_conf is not None and avg_conf < 0.85:
        out.append(Recommendation(
            rule_id="quality_low_confidence",
            severity="warning" if avg_conf >= 0.80 else "critical",
            category="jakość_predykcji",
            title="Niska pewność predykcji modelu",
            message=(
                f"Średnia pewność predykcji LSTM ({avg_conf:.2f}) jest poniżej progu 0.85, który koreluje "
                "z bezsensownymi współczynnikami w naszych testach. Rekomendacje poniżej traktuj ostrożnie."
            ),
            citation="(walidacja wewnętrzna — Iteracja 1)",
            detail=f"avg_confidence = {avg_conf:.3f}",
            suggestion="Nagraj kolejne ujęcie z lepszym oświetleniem / kadrem (cała sylwetka, brak zasłonięć).",
        ))

    # L/R steps asymmetry > 20%
    if n_left is not None and n_right is not None and (n_left + n_right) > 0:
        steps_si = 200 * abs(n_left - n_right) / (n_left + n_right)
        if steps_si > 20:
            out.append(Recommendation(
                rule_id="quality_steps_asymmetry",
                severity="critical",
                category="jakość_predykcji",
                title="Model myli kontakty L/P (steps asymmetry > 20%)",
                message=(
                    f"Wykryto {n_left} kontaktów lewej stopy i {n_right} prawej. To >20% asymetria liczby kroków, "
                    "która zwykle oznacza, że klasyfikator faz myli LEFT_STANCE z RIGHT_STANCE w części cykli. "
                    "Współczynniki opierające się na podziale L/P (GCT L vs R, symetria) są w tej sytuacji niewiarygodne."
                ),
                citation="(walidacja wewnętrzna — Iteracja 1, film 02)",
                detail=f"L={n_left}, R={n_right} (SI_steps={steps_si:.1f}%)",
                suggestion="Sprawdź jakość detekcji MediaPipe w tym ujęciu. Jeżeli sylwetka jest w pełni widoczna, "
                           "może to być limitacja modelu dla tego konkretnego biegacza.",
            ))

    # Max SI > 30%
    if max_si is not None and max_si > 30:
        out.append(Recommendation(
            rule_id="quality_max_si_high",
            severity="warning",
            category="jakość_predykcji",
            title="Bardzo wysoka maksymalna asymetria",
            message=(
                f"Max Symmetry Index = {max_si:.1f}% (próg 'potencjalnego problemu' to 10%). W połączeniu "
                "z niską confidence lub asymetrią kroków, prawdopodobnie artefakt predykcji, nie biegacza."
            ),
            citation="Robinson et al. 1987",
            detail=f"max SI = {max_si:.1f}%",
        ))

    return out


# -----------------------------------------------------------------------------
# Orchestrator
# -----------------------------------------------------------------------------

def generate_recommendations(
    meta: dict,
    temporal: dict,
    spatial: dict,
    symmetry: dict,
) -> dict:
    """Generuje listę rekomendacji ze wszystkich reguł, posortowaną wg severity.

    Args:
        meta: zawartość *-meta.json (zawiera avg_confidence, model_test_acc, fps, ...)
        temporal: *-temporal.json
        spatial: *-spatial.json
        symmetry: *-symmetry.json

    Returns:
        {"recommendations": [list[dict]], "summary": {...}}
    """
    all_recs: list[Recommendation] = []

    # Jakość predykcji najpierw — użytkownik powinien zobaczyć to zanim zacznie czytać szczegóły
    all_recs.extend(check_data_quality(meta, temporal, symmetry))

    all_recs.extend(check_cadence(temporal))
    all_recs.extend(check_gct(temporal))
    all_recs.extend(check_flight(temporal))
    all_recs.extend(check_duty_factor(temporal))
    all_recs.extend(check_torso_lean(spatial))
    all_recs.extend(check_knee_at_contact(spatial))
    all_recs.extend(check_vertical_oscillation(spatial))
    all_recs.extend(check_symmetry(symmetry))
    all_recs.extend(check_foot_strike(spatial, symmetry))

    # Sort: critical → warning → watch → info; potem zachowaj kolejność wstawienia
    all_recs.sort(key=lambda r: _SEVERITY_ORDER[r.severity])

    summary = {
        "total": len(all_recs),
        "critical": sum(1 for r in all_recs if r.severity == "critical"),
        "warning": sum(1 for r in all_recs if r.severity == "warning"),
        "watch": sum(1 for r in all_recs if r.severity == "watch"),
        "info": sum(1 for r in all_recs if r.severity == "info"),
    }

    return {
        "recommendations": [asdict(r) for r in all_recs],
        "summary": summary,
    }


if __name__ == "__main__":
    # Smoke test — wczytaj JSON-y Adama i wypisz rekomendacje
    import json
    from pathlib import Path

    base = Path("data/inference/24-adam")
    meta_path = base.parent / "24-adam-temporal.json"  # Adam nie ma meta.json (znany problem)
    if not meta_path.exists():
        print(f"Brak: {meta_path}")
        raise SystemExit(1)

    temporal = json.loads((base.parent / "24-adam-temporal.json").read_text(encoding="utf-8"))
    spatial = json.loads((base.parent / "24-adam-spatial.json").read_text(encoding="utf-8"))
    symmetry = json.loads((base.parent / "24-adam-symmetry.json").read_text(encoding="utf-8"))
    meta = {"avg_confidence": 0.909}  # z notatek (Adam meta.json nie był wygenerowany w MVP)

    result = generate_recommendations(meta, temporal, spatial, symmetry)
    print(f"Total: {result['summary']}")
    for r in result["recommendations"]:
        print(f"  [{r['severity']:8s}] {r['category']:18s} | {r['title']}")
