# Rekomendacje treningowe

**Wideo**: 22 - Running Analysis with Physiotherapist
**Pewność predykcji modelu**: 0.89

## Podsumowanie

- 🔴 Krytyczne: **0**  🟠 Ostrzeżenia: **3**  🟡 Do monitorowania: **5**  ℹ️ Informacje: **2**
- Łącznie reguł zwracających wynik: 10

## 🟠 Ostrzeżenie

### Bardzo wysoka maksymalna asymetria
*Kategoria: **jakość_predykcji** · Źródło: Robinson et al. 1987*

Max Symmetry Index = 35.0% (próg 'potencjalnego problemu' to 10%). W połączeniu z niską confidence lub asymetrią kroków, prawdopodobnie artefakt predykcji, nie biegacza.

**Pomiar**: max SI = 35.0%

---

### GCT lewa: przedłużony
*Kategoria: **GCT** · Źródło: Souza 2016; Heiderscheit et al. 2011*

GCT lewa w zakresie 280–350 ms wskazuje na wolne tempo lub długi krok. U biegaczy rekreacyjnych zalecane 220–280 ms — krótszy GCT poprawia ekonomię biegu.

**Pomiar**: GCT lewa: 285 ms

**Sugestia**: Spróbuj zwiększyć kadencję o ~5–10% — zwykle skraca GCT bez wysiłku.

---

### Asymetria L/P powyżej 10% — rozważ konsultację
*Kategoria: **symetria** · Źródło: Robinson et al. 1987; Souza 2016*

Wskaźnik symetrii Robinsona (SI = 200·|L−R|/(L+R)) powyżej 10% literatura traktuje jako sygnał potencjalnego dysbalansu mięśniowego lub kompensacji po przebytej kontuzji. UWAGA: część asymetrii w danych monocularnych 2D może być artefaktem perspektywy (strona bliżej kamery wydaje się ruszać 'większą amplitudą').

**Pomiar**: GCT (czas kontaktu) SI=22.8%; duty factor SI=21.4%; kąt kolana w fazie stance SI=35.0%

**Sugestia**: Jeżeli asymetria utrzymuje się na innych nagraniach, konsultacja z fizjoterapeutą.

---

## 🟡 Do monitorowania

### Kadencja rekreacyjna — możliwość poprawy
*Kategoria: **kadencja** · Źródło: Heiderscheit et al. 2011*

Kadencja w zakresie 160–170 spm jest typowa dla biegaczy rekreacyjnych. Stopniowe podniesienie do 170–180 spm może zmniejszyć obciążenie stawów.

**Pomiar**: kadencja: 163 spm

**Sugestia**: Cel długoterminowy: 170–180 spm. Wprowadzaj zmianę stopniowo (~5%/tydzień).

---

### Kolano lewa przy kontakcie: zbyt ugięte ('siedzący' bieg)
*Kategoria: **kolano@kontakt** · Źródło: Novacheck 1998*

Kąt kolana < 155° przy kontakcie wskazuje na 'siedzący' wzorzec biegu — więcej pracy mięśni przy każdym kroku, mniejsze wykorzystanie energii elastycznej ścięgien. UWAGA: bardzo niskie wartości (<100°) zwykle oznaczają błąd predykcji klatki kontaktu.

**Pomiar**: kąt kolana lewa: 98.2°

---

### Kolano prawa przy kontakcie: zbyt ugięte ('siedzący' bieg)
*Kategoria: **kolano@kontakt** · Źródło: Novacheck 1998*

Kąt kolana < 155° przy kontakcie wskazuje na 'siedzący' wzorzec biegu — więcej pracy mięśni przy każdym kroku, mniejsze wykorzystanie energii elastycznej ścięgien. UWAGA: bardzo niskie wartości (<100°) zwykle oznaczają błąd predykcji klatki kontaktu.

**Pomiar**: kąt kolana prawa: 137.4°

---

### Bardzo niska oscylacja pionowa
*Kategoria: **vert_osc** · Źródło: Diaz et al. 2019*

Oscylacja < 0.12 torso jest nietypowa — może być wynikiem szumu keypointów MediaPipe (brak czubka głowy, biodro zasłonięte) lub bardzo płaskiego, krótkiego kroku.

**Pomiar**: vert osc / torso: 0.100

---

### Łagodna asymetria L/P (5–10%)
*Kategoria: **symetria** · Źródło: Robinson et al. 1987*

Wskaźnik symetrii Robinsona 5–10% to wartość 'do monitorowania' — drobne różnice między nogami są powszechne u rekreacyjnych biegaczy, ale warto obserwować trend w czasie.

**Pomiar**: kąt kostki w fazie stance SI=7.2%

---

## ℹ️ Informacja

### Pochylenie tułowia prawidłowe
*Kategoria: **tułów** · Źródło: Novacheck 1998*

Pochylenie tułowia w zakresie 5–15° to optymalne wykorzystanie grawitacji w biegu.

**Pomiar**: pochylenie: 9.9°

---

### Spójny wzorzec lądowania (forefoot strike)
*Kategoria: **foot_strike** · Źródło: Daoud et al. 2012*

Obie stopy lądują tym samym wzorcem (forefoot strike). Literatura nie wskazuje jednoznacznie 'najlepszego' wzorca foot strike u dorosłych biegaczy — istotniejsza jest stabilność wzorca i brak overstridingu.

**Pomiar**: L=P=forefoot strike

---


_Rekomendacje są generowane przez reguły z literatury biomechanicznej (Heiderscheit 2011, Novacheck 1998, Souza 2016, Diaz 2019, Robinson 1987, Daoud 2012) — nie zastępują konsultacji specjalisty. Pełne progi i źródła: `docs/reference-values.md`._
