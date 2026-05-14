# 2026-05-14 — Setup LaTeX dla pracy magisterskiej + optymalizacja kosztów Claude

## Status

**Decyzja odłożona** — user czeka na **template LaTeX od uczelni / promotora**
przed utworzeniem struktury `thesis/`. Niniejsza notatka zachowuje rekomendację
i wytyczne, by w kolejnej sesji nie zaczynać dyskusji od zera.

## Rekomendacja: subdirectory `thesis/` w tym projekcie (NIE osobny projekt)

### Uzasadnienie

1. **Pełny kontekst Claude'a za darmo** — gdy piszę rozdział o wrażliwości, agent
   automatycznie widzi CLAUDE.md, `docs/thesis-notes/`, dane w `data/inference/`,
   kod w `src/`. Bez kopiowania.
2. **Auto-memory działa** — konwencja zapisywania wyjaśnień konceptualnych
   ([[feedback-zapisuj-wyjasnienia-konceptualne]]) już ustawiona dla tego projektu.
3. **Pojedyncze repo = pojedyncza prawda** — nowa notatka w `thesis-notes/`
   natychmiast dostępna do cytowania, bez synchronizacji między repo.

Osobny projekt LaTeX miałby sens tylko gdyby praca była długoterminowa, niezwiązana
z tym kodem, lub miała innych kolaborantów — żadne z tego nie zachodzi.

## Proponowana struktura folderu (gdy zaczynamy)

```
running-analysis/
├── ...                                   (istniejące katalogi — bez zmian)
└── thesis/                               ← do utworzenia w przyszłej sesji
    ├── main.tex                          (preambula, includes, abstract)
    ├── chapters/
    │   ├── 01-wstep.tex
    │   ├── 02-state-of-the-art.tex
    │   ├── 03-materialy-metody.tex
    │   ├── 04-klasyfikator.tex
    │   ├── 05-wspolczynniki.tex
    │   ├── 06-rekomendacje.tex
    │   ├── 07-wrazliwosc.tex
    │   └── 08-dyskusja-wnioski.tex
    ├── figures/                          (kopia/symlink z docs/thesis-notes/figures/)
    ├── references.bib                    (~25-30 referencji)
    ├── chapter-summaries/                ← klucz dla kosztów (patrz niżej)
    │   ├── 01-summary.md                 (1-stronicowe streszczenie ukończonego rozdziału)
    │   └── ...
    └── README.md                         (jak kompilować, konwencje)
```

Plus `.gitignore` dla artefaktów LaTeX: `*.aux`, `*.log`, `*.pdf`, `*.bbl`, `*.bcf`,
`*.fdb_latexmk`, `*.fls`, `*.out`, `*.synctex.gz`, `*.toc`, `*.lof`, `*.lot`.

## Template LaTeX

**Decyzja użytkownika**: czekamy na **template uczelni / promotora**. Gdy będzie
dostępny:
- Wkleić do `thesis/` (lub jako submodule, zależnie od formatu)
- Dostosować strukturę 8 rozdziałów z [[temat-pracy-finalny]] do układu template'u
- Jeśli template ma własne `main.tex` — adoptujemy, własnego nie tworzymy

## 7 technik optymalizacji kosztów Claude'a podczas pisania

### 1. Jedna sesja = jeden rozdział

Otwierać **nową sesję Claude Code** na każdy rozdział. Wtedy kontekst ma tylko to,
co potrzebne (CLAUDE.md auto + notatki thesis dla tego rozdziału). Stara sesja po
prostu zapomnij — auto-memory przeniesie kluczowe wnioski.

### 2. Chapter summaries (~1 strona każdy)

Po ukończeniu rozdziału X, zapisać w `thesis/chapter-summaries/0X-summary.md`:
- 3-5 zdań co jest w tym rozdziale
- Kluczowe liczby/wnioski (z cytowaniem artefaktu źródłowego)
- Co jest cytowane w innych rozdziałach

Gdy piszę rozdział 7, ładuję **summary** rozdz. 4 (~1 strona), nie pełną treść
(~10 stron). Oszczędność: ~80% tokenów na cross-references.

### 3. Konkretne zadania, nie "napisz rozdział X"

- **Źle**: *"Napisz cały rozdział 4 (porównanie klasyfikatorów)"*
- **Dobrze**: *"Napisz sekcję 4.2 (Confusion matrices + per-film breakdown),
  max 600 słów, na podstawie `figures/per_file_test.md` i
  `figures/confusion_matrices_test.png`"*

Krótkie zadania = mniej output tokens = niższy koszt. Pełny rozdział pisać
w 5-8 podzadaniach.

### 4. Bibliografia raz, używaj przez całą pracę

Stworzyć `references.bib` na początku z **25-30 wpisami BibTeX** (z researchu
2026-05-14: Stenum, Ali, Ripic, HGcnMLP, Frontiers Phys 2025, Bouchabou, Hannigan
+ biomechaniczne Heiderscheit, Souza, Novacheck, Diaz, Robinson, Daoud + technical
MediaPipe BlazePose Bazarevsky 2020, COCO Lin 2014, OpenPose Cao 2018).

Potem cytujemy `\cite{stenum2021}` — agent nie musi re-czytać bibliografii za
każdym razem.

### 5. Edit, nie Write, dla istniejących plików

Gdy proszę o poprawkę w rozdziale 4, agent używa Edit (wysyła tylko diff), nie
Write (cały plik). Drobny szczegół, ale przy 60 stronach pracy sumuje się.

### 6. Prompt caching wykorzystywany automatycznie

Claude Code wykorzystuje **prompt caching** Anthropic API — gdy CLAUDE.md jest
ładowany w kolejnych zapytaniach tej samej sesji, jest **~5× tańszy** (cache hit).

**Konsekwencja**: długie sesje z wieloma turami w jednym rozdziale są tańsze niż
krótkie sesje per turę. Brzmi paradoksalnie wobec techniki #1, ale obie prawdziwe:
- **Per rozdział = osobna sesja** (jasny kontekst, zapobiega rozdmuchaniu)
- **W obrębie rozdziału = wiele tur, nie pojedyncze pytania** (cache hits)

### 7. Memory entries dla preferencji stylu

Po pierwszej sesji pisania zapisać preferencje w `memory/` jako feedback entries:
- *"Pisz po polsku, formalnie, nie używaj zaimków pierwszej osoby"*
- *"Cytuj zawsze `\cite{key}` przed kropką, nie po"*
- *"Tabele numeruj Tabela X.Y (rozdział.numer)"*
- *"Każda konkretna liczba musi mieć cytat artefaktu źródłowego"*
  (już ustalone w korekcie 3 z notatki wyjaśnień)

Wtedy w każdej kolejnej sesji agent zna konwencje od pierwszej tury.

## Szacunkowe koszty (Sonnet 4.6 + prompt caching)

| Scenariusz | Sesje | Tokeny / sesja | Razem |
|---|---|---|---|
| Wszystko w jednej sesji (źle) | 1 | 200k+ | ~$15+ |
| Sesja per rozdział (8 sesji) | 8 | ~30k | ~$5-8 |
| Sesja per rozdział + chapter summaries | 8 | ~20k | ~$3-5 |
| + prompt caching effects | 8 | ~12-15k effective | **~$2-3** |

Szacunki bardzo zgrubne. **Opus 4.7** byłby ~5× droższy, ale daje lepszą jakość
pisania — dla rozdziałów kluczowych (4 Klasyfikator, 5 Współczynniki, 8 Dyskusja)
warto Opus. Dla wstępu, SoTA, biograficznych można Sonnet.

## Praktyczne wytyczne na pierwszą sesję pisania

1. **Najpierw template uczelni** — bez tego nie zaczynamy struktury (uniknąć
   przerabiania późniejszego).
2. **Pierwsza rzecz po template**: utworzyć `references.bib` z 25-30 wpisami.
3. **Pierwszy rozdział do napisania**: rozdz. 3 (Materiały i metody) — pisać przed 1
   i 2, bo wszystkie liczby/decyzje są obiektywne, łatwe do napisania. Wstęp
   i SoTA wymagają większej narracji, lepiej je pisać gdy reszta pracy istnieje.
4. **Sekcja "co jest gotowe"** po każdym rozdziale: dopisać do `chapter-summaries/`
   żeby kolejne sesje miały punkt startowy.

## Powiązane notatki

- [[temat-pracy-finalny]] — tytuł, 3 pytania, 7 hipotez, struktura 8 rozdziałów
- [[research-podobnych-prac]] — 7 prac do bibliografii
- [[wyjasnienia-pojec-do-pisania]] — fragmenty do wstępu/metodologii
- [[feedback-zapisuj-wyjasnienia-konceptualne]] — auto-memory konwencja
