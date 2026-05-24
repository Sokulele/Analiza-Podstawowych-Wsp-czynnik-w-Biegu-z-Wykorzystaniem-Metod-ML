# Praca magisterska — SGGW

**Tytuł**: Analiza podstawowych współczynników biegu przy pomocy uczenia maszynowego

**Szablon**: [SGGW-Thesis-LaTeX](https://github.com/lchmiel/SGGW-Thesis-LaTeX) (klasa `SGGW-thesis.cls`, autor Łukasz Adamczyk)

## Struktura

```
Thesis/
├── main.tex                       — preambuła, metadane, includes rozdziałów
├── SGGW-thesis.cls                — klasa LaTeX SGGW (NIE modyfikować)
├── naglowek_mgr.png               — nagłówek dla magisterki
├── stopka_WZIM.png                — stopka WZIM
├── chapters/
│   ├── 01-wstep.tex
│   ├── 02-state-of-the-art.tex
│   ├── 03-materialy-metody.tex    ← rekomendowane: pisać jako PIERWSZY
│   ├── 04-klasyfikator.tex
│   ├── 05-wspolczynniki.tex       ← centralny rozdział wg tytułu pracy
│   ├── 06-rekomendacje.tex
│   ├── 07-wrazliwosc.tex
│   ├── 08-dyskusja-wnioski.tex
│   └── bibliography.tex           — wpisy `\bibitem` (ręczny `thebibliography`)
├── figures/                       — wykresy/obrazy do wstawienia
├── TEMPLATE-README.md             — oryginalny README szablonu SGGW (referencja)
├── TEMPLATE-README.txt            — j.w.
└── .gitignore                     — artefakty LaTeX (*.aux, *.log, *.pdf, ...)
```

## Co zrobione w setupie

- [x] Sklonowany szablon SGGW
- [x] Flaga `\MAGISTERSKAtrue` (zamiast domyślnej `\INZYNIERSKAtrue`)
- [x] Flaga `\WZIMtrue` dla wydziału
- [x] Tytuł pracy (PL + EN) w `main.tex`
- [x] Struktura 8 rozdziałów rozdzielona na osobne pliki w `chapters/`
- [x] Szkielet każdego rozdziału z sekcjami i komentarzami TODO
- [x] Bibliografia szkieletowa (`chapters/bibliography.tex`) — 20+ wpisów z researchu
- [x] `.gitignore` dla artefaktów LaTeX

## Co wymaga uzupełnienia przed kompilacją

W `main.tex` (linie 9-15) zostawiłem placeholdery — uzupełnij:

- `\author{Imię Nazwisko}` — Twoje dane
- `\date{2026}` — rok obrony
- `\album{000000}` — numer albumu
- `\promotor{<tytuł> <Imię Nazwisko>}` — dane promotora
- `\pworkplace{Instytut... Katedra...}` — miejsce pracy promotora
- `\course{Informatyka}` — potwierdź kierunek

Plus streszczenia (PL + EN) w `main.tex` — pisać **na końcu**, gdy reszta pracy gotowa.

## Kompilacja

Wymagana dystrybucja LaTeX (MiKTeX / TeX Live) + Polish locale.

```bash
# Trzykrotna kompilacja (zalecane dla spisu treści + bibliografii):
pdflatex main.tex
pdflatex main.tex
pdflatex main.tex
```

Lub w `latexmk`:

```bash
latexmk -pdf main.tex
```

Wynik: `main.pdf` (ignorowany przez git, jeśli chcesz wersjonować PDF — odkomentuj
linię w `.gitignore`).

## Konwencje pisania

Każdy plik rozdziału (`chapters/0X-*.tex`) zawiera:
- Komentarz `% TODO:` na początku — co napisać, gdzie znaleźć materiał źródłowy
  (zwykle pointery do notatek w `../docs/thesis-notes/`)
- Strukturę sekcji (`\section{...}` + `\label{sec:...}`)
- Komentarze `% TODO:` w sekcjach — konkretne wytyczne co opisać

## Powiązane materiały

- **Wytyczna główna**: `../docs/thesis-notes/2026-05-14-temat-pracy-finalny.md`
- **Research literatury**: `../docs/thesis-notes/2026-05-14-research-podobnych-prac.md`
- **Wyjaśnienia pojęć (rosnący dokument)**: `../docs/thesis-notes/2026-05-14-wyjasnienia-pojec-do-pisania.md`
- **Setup + optymalizacja kosztów Claude**: `../docs/thesis-notes/2026-05-14-setup-latex-i-koszty.md`
- **Wszystkie notatki**: `../docs/thesis-notes/README.md`
- **Wyniki eksperymentów**: `../docs/thesis-notes/figures/`

## Strategia pisania (rekomendowana)

1. **Najpierw uzupełnij metadane** w `main.tex` (autor, promotor, album)
2. **Skompiluj pusty szkielet** — sprawdź czy LaTeX działa, czy nagłówek/stopka są OK
3. **Pisz rozdział 3 jako PIERWSZY** (Materiały i metody — najłatwiejszy, obiektywny)
4. **Potem rozdziały 4-7** (eksperymenty, mają pełny materiał empiryczny)
5. **Rozdziały 1-2 (Wstęp + SoTA) NA KOŃCU** — wymagają większej narracji
6. **Streszczenia + spis literatury** uzupełniaj w trakcie, finalizuj na końcu

**Jedna sesja Claude = jeden rozdział** (optymalizacja kosztów — patrz
`../docs/thesis-notes/2026-05-14-setup-latex-i-koszty.md`).
