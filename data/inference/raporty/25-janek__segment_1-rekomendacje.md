# Rekomendacje treningowe

**Wideo**: 25 - janek__segment_1
**Pewność predykcji modelu**: 0.88

## Podsumowanie

- 🔴 Krytyczne: **2**  🟠 Ostrzeżenia: **3**  🟡 Do monitorowania: **3**  ℹ️ Informacje: **2**
- Łącznie reguł zwracających wynik: 10

## 🔴 Krytyczne

### Kadencja bardzo niska
*Kategoria: **kadencja** · Źródło: Heiderscheit et al. 2011; Novacheck 1998*

Kadencja poniżej 150 spm odbiega od typowego zakresu biegu (150–185 spm). Może oznaczać overstriding lub przejście w chód. Sprawdź, czy materiał wideo rzeczywiście pokazuje bieg ciągły.

**Pomiar**: kadencja zmierzona: 148 spm, cel: 170–180 spm

**Sugestia**: Skróć krok i zwiększ częstość kontaktów (~+15–20 spm), tak aby zbliżyć się do 170 spm.

---

### GCT prawa: bardzo długi czas kontaktu
*Kategoria: **GCT** · Źródło: Souza 2016*

GCT prawa > 350 ms sugeruje jogging na pograniczu chodu albo błąd predykcji fazy. Długi GCT silnie zwiększa obciążenie stawów.

**Pomiar**: GCT prawa: 357 ms (typowy bieg rekreacyjny: 220–280 ms)

**Sugestia**: Zwiększ kadencję — krótszy krok skraca czas kontaktu z podłożem.

---

## 🟠 Ostrzeżenie

### Bardzo wysoka maksymalna asymetria
*Kategoria: **jakość_predykcji** · Źródło: Robinson et al. 1987*

Max Symmetry Index = 60.0% (próg 'potencjalnego problemu' to 10%). W połączeniu z niską confidence lub asymetrią kroków, prawdopodobnie artefakt predykcji, nie biegacza.

**Pomiar**: max SI = 60.0%

---

### Sygnał overstriding (niska kadencja + długi GCT)
*Kategoria: **GCT** · Źródło: Heiderscheit et al. 2011; Novacheck 1998*

Połączenie kadencji < 160 spm i średniego GCT > 270 ms jest klasycznym wzorcem overstridingu — stopa ląduje znacznie przed środkiem ciężkości, co zwiększa siły hamowania i obciążenie kolan.

**Pomiar**: kadencja 148 spm, GCT średni 275 ms

**Sugestia**: Zwiększ kadencję o 5–10% — to najczęstszy zalecany sposób korekcji overstridingu.

---

### Asymetria L/P powyżej 10% — rozważ konsultację
*Kategoria: **symetria** · Źródło: Robinson et al. 1987; Souza 2016*

Wskaźnik symetrii Robinsona (SI = 200·|L−R|/(L+R)) powyżej 10% literatura traktuje jako sygnał potencjalnego dysbalansu mięśniowego lub kompensacji po przebytej kontuzji. UWAGA: część asymetrii w danych monocularnych 2D może być artefaktem perspektywy (strona bliżej kamery wydaje się ruszać 'większą amplitudą').

**Pomiar**: GCT (czas kontaktu) SI=59.9%; duty factor SI=60.0%

**Sugestia**: Jeżeli asymetria utrzymuje się na innych nagraniach, konsultacja z fizjoterapeutą.

---

## 🟡 Do monitorowania

### Kolano lewa przy kontakcie: zbyt ugięte ('siedzący' bieg)
*Kategoria: **kolano@kontakt** · Źródło: Novacheck 1998*

Kąt kolana < 155° przy kontakcie wskazuje na 'siedzący' wzorzec biegu — więcej pracy mięśni przy każdym kroku, mniejsze wykorzystanie energii elastycznej ścięgien. UWAGA: bardzo niskie wartości (<100°) zwykle oznaczają błąd predykcji klatki kontaktu.

**Pomiar**: kąt kolana lewa: 138.0°

---

### Kolano prawa przy kontakcie: zbyt ugięte ('siedzący' bieg)
*Kategoria: **kolano@kontakt** · Źródło: Novacheck 1998*

Kąt kolana < 155° przy kontakcie wskazuje na 'siedzący' wzorzec biegu — więcej pracy mięśni przy każdym kroku, mniejsze wykorzystanie energii elastycznej ścięgien. UWAGA: bardzo niskie wartości (<100°) zwykle oznaczają błąd predykcji klatki kontaktu.

**Pomiar**: kąt kolana prawa: 148.5°

---

### Bardzo niska oscylacja pionowa
*Kategoria: **vert_osc** · Źródło: Diaz et al. 2019*

Oscylacja < 0.12 torso jest nietypowa — może być wynikiem szumu keypointów MediaPipe (brak czubka głowy, biodro zasłonięte) lub bardzo płaskiego, krótkiego kroku.

**Pomiar**: vert osc / torso: 0.110

---

## ℹ️ Informacja

### Pochylenie tułowia prawidłowe
*Kategoria: **tułów** · Źródło: Novacheck 1998*

Pochylenie tułowia w zakresie 5–15° to optymalne wykorzystanie grawitacji w biegu.

**Pomiar**: pochylenie: 9.9°

---

### Spójny wzorzec lądowania (midfoot strike)
*Kategoria: **foot_strike** · Źródło: Daoud et al. 2012*

Obie stopy lądują tym samym wzorcem (midfoot strike). Literatura nie wskazuje jednoznacznie 'najlepszego' wzorca foot strike u dorosłych biegaczy — istotniejsza jest stabilność wzorca i brak overstridingu.

**Pomiar**: L=P=midfoot strike

---


_Rekomendacje są generowane przez reguły z literatury biomechanicznej (Heiderscheit 2011, Novacheck 1998, Souza 2016, Diaz 2019, Robinson 1987, Daoud 2012) — nie zastępują konsultacji specjalisty. Pełne progi i źródła: `docs/reference-values.md`._
