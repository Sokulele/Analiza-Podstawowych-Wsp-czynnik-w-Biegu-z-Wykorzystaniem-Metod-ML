# Rekomendacje treningowe

**Wideo**: 02 - Running at 13km⧸h - Side View
**Pewność predykcji modelu**: 0.80

## Podsumowanie

- 🔴 Krytyczne: **4**  🟠 Ostrzeżenia: **4**  🟡 Do monitorowania: **6**  ℹ️ Informacje: **1**
- Łącznie reguł zwracających wynik: 15

## 🔴 Krytyczne

### Niska pewność predykcji modelu
*Kategoria: **jakość_predykcji** · Źródło: (walidacja wewnętrzna — Iteracja 1)*

Średnia pewność predykcji LSTM (0.80) jest poniżej progu 0.85, który koreluje z bezsensownymi współczynnikami w naszych testach. Rekomendacje poniżej traktuj ostrożnie.

**Pomiar**: avg_confidence = 0.795

**Sugestia**: Nagraj kolejne ujęcie z lepszym oświetleniem / kadrem (cała sylwetka, brak zasłonięć).

---

### Model myli kontakty L/P (steps asymmetry > 20%)
*Kategoria: **jakość_predykcji** · Źródło: (walidacja wewnętrzna — Iteracja 1, film 02)*

Wykryto 14 kontaktów lewej stopy i 10 prawej. To >20% asymetria liczby kroków, która zwykle oznacza, że klasyfikator faz myli LEFT_STANCE z RIGHT_STANCE w części cykli. Współczynniki opierające się na podziale L/P (GCT L vs R, symetria) są w tej sytuacji niewiarygodne.

**Pomiar**: L=14, R=10 (SI_steps=33.3%)

**Sugestia**: Sprawdź jakość detekcji MediaPipe w tym ujęciu. Jeżeli sylwetka jest w pełni widoczna, może to być limitacja modelu dla tego konkretnego biegacza.

---

### Wiele sygnałów niskiej jakości predykcji (combinatorical)
*Kategoria: **jakość_predykcji** · Źródło: (walidacja wewnętrzna — Janek edge case, 2026-05-12)*

Bardzo wysoka asymetria (max SI = 96.5%) **w połączeniu** z niepewnością predykcji (avg_conf = 0.80) silnie sugeruje, że model myli granice STANCE per noga w części cykli — nawet jeśli liczby kroków L/R są zbalansowane. Współczynniki L/P (GCT L vs R, duty factor L/R, symetria) są w tej sytuacji niewiarygodne.

**Pomiar**: max SI = 96.5%, avg_conf = 0.795, steps_SI = 33.3%

**Sugestia**: Nagraj kolejne ujęcie z lepszym kadrem (cała sylwetka, brak okluzji bioder/stóp). Współczynniki agregaty (kadencja, GCT średni) pozostają wiarygodne, ale interpretacja L vs P jest podejrzana.

---

### Kadencja bardzo niska
*Kategoria: **kadencja** · Źródło: Heiderscheit et al. 2011; Novacheck 1998*

Kadencja poniżej 150 spm odbiega od typowego zakresu biegu (150–185 spm). Może oznaczać overstriding lub przejście w chód. Sprawdź, czy materiał wideo rzeczywiście pokazuje bieg ciągły.

**Pomiar**: kadencja zmierzona: 144 spm, cel: 170–180 spm

**Sugestia**: Skróć krok i zwiększ częstość kontaktów (~+15–20 spm), tak aby zbliżyć się do 170 spm.

---

## 🟠 Ostrzeżenie

### Bardzo wysoka maksymalna asymetria
*Kategoria: **jakość_predykcji** · Źródło: Robinson et al. 1987*

Max Symmetry Index = 96.5% (próg 'potencjalnego problemu' to 10%). W połączeniu z niską confidence lub asymetrią kroków, prawdopodobnie artefakt predykcji, nie biegacza.

**Pomiar**: max SI = 96.5%

---

### Overstride: długi krok + niska kadencja
*Kategoria: **stride_length** · Źródło: Heiderscheit et al. 2011*

Stride > 2.2 m przy kadencji < 160 spm to wyraźny wzorzec overstridingu — stopa ląduje znacznie przed środkiem ciężkości, co generuje duże siły hamowania w kolanie i biodrze. Krótszy krok z wyższą kadencją zwykle wystarczy do korekcji.

**Pomiar**: stride 2.83 m, kadencja 144 spm

**Sugestia**: Zwiększ kadencję o 5–10% — automatycznie skróci stride przy tej samej prędkości bieżni.

---

### Asymetria L/P powyżej 10% — rozważ konsultację
*Kategoria: **symetria** · Źródło: Robinson et al. 1987; Souza 2016*

Wskaźnik symetrii Robinsona (SI = 200·|L−R|/(L+R)) powyżej 10% literatura traktuje jako sygnał potencjalnego dysbalansu mięśniowego lub kompensacji po przebytej kontuzji. UWAGA: część asymetrii w danych monocularnych 2D może być artefaktem perspektywy (strona bliżej kamery wydaje się ruszać 'większą amplitudą').

**Pomiar**: GCT (czas kontaktu) SI=62.0%; czas cyklu SI=40.6%; duty factor SI=96.5%; kąt kolana w fazie stance SI=26.6%; kąt kostki w fazie stance SI=10.8%

**Sugestia**: Jeżeli asymetria utrzymuje się na innych nagraniach, konsultacja z fizjoterapeutą.

---

### Różne wzorce lądowania L/P: midfoot strike vs forefoot strike
*Kategoria: **foot_strike** · Źródło: Daoud et al. 2012; Souza 2016*

Lewa stopa ląduje wzorcem 'midfoot strike', prawa wzorcem 'forefoot strike'. Różny wzorzec L/P sugeruje kompensację (np. po dawnej kontuzji), choć może też być artefaktem aspect ratio lub szumu keypointów stóp w MediaPipe.

**Pomiar**: L: midfoot strike, P: forefoot strike

**Sugestia**: Sprawdź wzrokowo kilka klatek initial contact. Jeśli wzorzec rzeczywisty, warto skonsultować ze specjalistą.

---

## 🟡 Do monitorowania

### GCT prawa: nietypowo krótki
*Kategoria: **GCT** · Źródło: Souza 2016*

GCT prawa < 150 ms typowy dla sprinterów elity. Dla biegu rekreacyjnego to wartość poza typowym zakresem — może być artefaktem predykcji fazy (model może mylić L/R lub fragmentaryzować STANCE).

**Pomiar**: GCT prawa: 130 ms

**Sugestia**: Zweryfikuj wzrokowo kilka cykli na materiale wideo.

---

### Duty factor prawa: bardzo niski
*Kategoria: **duty_factor** · Źródło: Souza 2016*

DF prawa < 0.22 typowy dla sprintów na pełnej prędkości. Dla biegu rekreacyjnego to wartość poza typowym zakresem — może być artefaktem predykcji.

**Pomiar**: DF prawa: 0.132

---

### Długi krok (stride 2.4–3.0 m)
*Kategoria: **stride_length** · Źródło: Heiderscheit et al. 2011; Novacheck 1998*

Stride 2.4–3.0 m typowy dla szybkiego biegu. Jeżeli kadencja jest niska, to może być sygnał overstridingu — patrz reguła łączona poniżej.

**Pomiar**: stride: 2.83 m

---

### Kolano lewa przy kontakcie: zbyt ugięte ('siedzący' bieg)
*Kategoria: **kolano@kontakt** · Źródło: Novacheck 1998*

Kąt kolana < 155° przy kontakcie wskazuje na 'siedzący' wzorzec biegu — więcej pracy mięśni przy każdym kroku, mniejsze wykorzystanie energii elastycznej ścięgien. UWAGA: bardzo niskie wartości (<100°) zwykle oznaczają błąd predykcji klatki kontaktu.

**Pomiar**: kąt kolana lewa: 149.8°

---

### Kolano prawa przy kontakcie: zbyt ugięte ('siedzący' bieg)
*Kategoria: **kolano@kontakt** · Źródło: Novacheck 1998*

Kąt kolana < 155° przy kontakcie wskazuje na 'siedzący' wzorzec biegu — więcej pracy mięśni przy każdym kroku, mniejsze wykorzystanie energii elastycznej ścięgien. UWAGA: bardzo niskie wartości (<100°) zwykle oznaczają błąd predykcji klatki kontaktu.

**Pomiar**: kąt kolana prawa: 100.7°

---

### Oscylacja pionowa — poziom rekreacyjny
*Kategoria: **vert_osc** · Źródło: Diaz et al. 2019*

Oscylacja w zakresie 0.16–0.24 torso (≈ 8–12 cm) jest typowa dla rekreacyjnych biegaczy. Stopniowe obniżenie poprawi ekonomię biegu.

**Pomiar**: vert osc / torso: 0.170

---

## ℹ️ Informacja

### Pochylenie tułowia prawidłowe
*Kategoria: **tułów** · Źródło: Novacheck 1998*

Pochylenie tułowia w zakresie 5–15° to optymalne wykorzystanie grawitacji w biegu.

**Pomiar**: pochylenie: 5.7°

---


_Rekomendacje są generowane przez reguły z literatury biomechanicznej (Heiderscheit 2011, Novacheck 1998, Souza 2016, Diaz 2019, Robinson 1987, Daoud 2012) — nie zastępują konsultacji specjalisty. Pełne progi i źródła: `docs/reference-values.md`._
