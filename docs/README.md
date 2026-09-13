# docs/

LaTeX izvor seminarskog rada *„Upravljanje zglobom Universal Robots robota pomoću
OptiTrack sustava u realnom vremenu"*.

## Struktura

```
docs/
├── main.tex          ← korijenski dokument (preambula, naslovnica, \input poglavlja)
├── references.bib    ← BibTeX baza (15 radova + norma ISO/TS 15066), stil ieeetr
├── chapters/         ← poglavlja 00-sazetak … 06-zakljucak
├── figures/          ← slike (.pdf za vektorske grafove, .png/.jpg za fotografije)
├── tables/           ← tablice kao zasebne .tex datoteke, generirane iz telemetrije
├── presentation/     ← prezentacija za obranu (.pptx, .pdf, vektorski asseti)
├── build/            ← privremeni izlaz kompilacije (ignoriran u gitu)
├── REVIEW.md         ← recenzija prije predaje: provjera brojki i formalnih zahtjeva
└── ANALIZA_REZULTATA_I_METRIKA.md
```

## Kompilacija

```powershell
./scripts/build-docs.ps1              # Windows
./scripts/build-docs.sh               # Linux / macOS
```

Skripta koristi **Tectonic** (ili `latexmk` kao zamjenu), kompilira `docs/main.tex`
i kopira rezultat u `dist/<verzija>/HRI_seminar_Kresimir_Hartl.pdf`
(zadana verzija: `v1`).

Korisne zastavice: `-Clean` (obriši međuprodukte), `-Engine tectonic|latexmk`,
`-Version v1` (odredište u `dist/`).

## Ograničenje opsega

Kolegij dopušta **najviše 12 stranica** i rad je trenutno **točno na tom limitu**.
Skripta ispisuje `Stranice: N / 12` na kraju builda — ako N prijeđe 12, build treba
smatrati neuspjelim. Svaka dopuna teksta mora biti kompenzirana skraćivanjem drugdje.

## Konvencije

- Jezik rada: hrvatski (`babel` s opcijom `croatian`); kod i komentari: engleski.
- Bez prelamanja riječi (`\hyphenpenalty=10000` u `main.tex`).
- Slike i tablice numeriraju se po poglavljima; jednostupčane tablice pinaju se s `[H]`
  da stoje uz tekst koji ih referencira, dvostupčani floatovi koriste `[t]`.
- Citati isključivo prema stvarnim PDF-ovima u `data/sources/` — bez izmišljenih ključeva.
