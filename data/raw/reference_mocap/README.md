# OptiTrack data — format, organizacija i parser-ugovor

OptiTrack (Motive) snimke pokreta ljudske šake koje napajaju real-time pipeline. Snimke se
tretiraju kao **nepromjenjiv referentni izvor** (po konvenciji — ne uređivati nakon kopiranja).

## Organizacija

```
data/optitrack/
├── test/                      # referentne snimke za development + replay (CSV → UDP)
│   ├── vjezbe_01/             # take_hri_studenti_01.csv          (marker: dlan umjesto zapesce)
│   └── vjezbe_02/             # hri_snimanje_vjezbe_02_{x,y,z}.csv (marker: zapesce — PRIMARNO)
└── (live/)                    # buduće: žive snimke s punog hardvera (isti format)

data/processed/<take>_<ddmmyyyy_hhmmss>/   # izvedeni artefakti (parsirano, kut, filtrirano,
                                           #   latency logovi). NIKAD pisati natrag u test/.
```

- **Primarni dataset: `vjezbe_02`** — sadrži marker `zapesce` (zapešće), nužan za hand-frame
  i kut fleksije. `x/y/z` su **tri zasebne snimke** (ne komponente!), različite duljine.
- **Sekundarni: `vjezbe_01`** — koristi `dlan` (dlan) umjesto `zapesce`; za test robusnosti
  parsera/kinematike na drugom marker-setu.

## Provenance
Kopirano iz kolegijskog repozitorija (`…/interakcija-covjeka-i-robota/vjezbe_optitrack/
data/optitrack_raw/`). Snimano na vježbama (Motive, Format Version 1.23). Originali ostaju
ondje; ovdje su radne kopije.

## Format CSV-a (Motive export) — PARSER UGOVOR

| Svojstvo | Vrijednost |
|---|---|
| Header redaka | **7** (metapodaci + nazivi); podaci počinju u **8. retku** |
| Stupci podataka | `Frame, Time(s), [X,Y,Z]×4 markera` = **14 stupaca** |
| Frekvencija snimanja | **120 Hz** (Δt ≈ 0.008333 s) — iz retka 1 "Capture Frame Rate" |
| Jedinice | **milimetri**; koordinatni prostor **Global** |
| Rotation type | Quaternion (mi koristimo samo pozicije markera) |

**Raspored header redaka:**
1. Metapodaci (`Format Version, Take Name, Capture Frame Rate, Total Frames in Take, Length Units…`)
2. (prazno)
3. `,Type,Marker,Marker,…`
4. `,Name,<set>:<marker>,…` ← **nazivi markera** (parser ih čita za mapiranje stupaca)
5. `,ID,…`
6. `,,Position,Position,…`
7. `Frame,Time (Seconds),X,Y,Z,X,Y,Z,…` ← zaglavlje podataka
8. → podaci

**Ključno za parser:** redak 4 (nazivi) i redci podataka (od 7) imaju **isto poravnanje
stupaca** (oba imaju prazan/`Frame` stupac na indeksu 0, `Time` na 1, prvi marker X na 2).
Zato se indeks naziva markera izravno koristi kao indeks stupca podatka — bez offseta.
Validacija: broj markera == 4, broj redaka == "Total Frames in Take", bez NaN.

## Marker setovi

| Dataset | Marker set | Markeri (X,Y,Z svaki) |
|---|---|---|
| `vjezbe_02` (primarno) | `MarkerSet 001` | `mali`, `palac`, `srednji`, **`zapesce`** |
| `vjezbe_01` (sekundarno) | `hri_studenti_ruka_01` | `mali`, `palac`, `srednji`, **`dlan`** |

Hand-frame (cross-product, ishodište = `zapesce`): X = zapešće→`srednji`; Z = X × (zapešće→
`mali`); Y = Z × X. Kut **fleksije** = jedna rotacijska komponenta orijentacije šake relativno
na referentni (početni) frame → mapira se na UR3e `wrist_1`/J4.

## Snimke (broj okvira)

| Datoteka | Okviri | Trajanje (~) |
|---|---|---|
| `vjezbe_02/…_x.csv` | 2452 | 20.4 s |
| `vjezbe_02/…_y.csv` | 2949 | 24.6 s |
| `vjezbe_02/…_z.csv` | 2549 | 21.2 s |
| `vjezbe_01/take_hri_studenti_01.csv` | 2116 | 17.6 s |
