# Subjektivni upitnik i evaluacijski obrazac (pHRI & Sense of Agency) — REZULTATI

**Datum sesije:** 2026-09-01 / 2026-09-02  
**Subjekt / Operater (odijelo i markeri):** Ivan Noršić  
**Promatrač / Inženjer (eksperiment i sigurnost):** Krešimir Hartl  
**Hardver:** Universal Robots UR3e (PolyScope 5.9.5, 125 Hz RTDE) + OptiTrack Motive 3.0.1 (120 Hz NatNet)  

---

## BLOK 1: Usporedba filtara na stvarnom robotu (T-04 – T-07)
*(T-04: One-Euro | T-05: Bez filtra `none` | T-06: Butterworth | T-07: EMA)*

### 👤 Odgovori Subjekta (Ivan Noršić):
- **Bez filtra (`none` / T-05)**: Robot je više trzao nego u T-04. Bilo je nervoznije upravljati, ali nije bilo primjetnog kašnjenja, već skokova.
- **One-Euro (`one_euro` / T-04)**: Najglađe upravljanje, nema osjetnog kašnjenja, mirno upravljanje u stacionarnom stanju. Pruža najsigurniji osjećaj vođenja.
- **Butterworth (T-06) i EMA (T-07)**: Primjetni skokovi i trzaji u odnosu na T-04, izraženo kašnjenje. Dolazak u ekstreme gibanja je isti, ali s kašnjenjem i trzajem pa je osjećaj sigurnosti smanjen. T-07 (EMA) je osjetno bolji po svemu od T-06 (Butterworth).
- **Subjektivni poredak / Pobjednik (Sense of Agency)**:
  1. **T-04 (One-Euro)** — apsolutni pobjednik
  2. **T-07 (EMA)**
  3. **T-05 (Bez filtra / `none`)**
  4. **T-06 (Butterworth)**

### 👁️ Zapažanja Promatrača (Krešimir Hartl):
- **Vizualni dojam i zvuk motora**: Nema znatne razlike u zvukovima motora, ali T-05 najviše kontinuirano trza (mikrootkloni), dok T-06 najviše skače i kasni pri promjenama smjera.
- **Stabilnost trajektorije**: T-04 (One-Euro) je najfluidniji i najprirodniji sa strane.

---

## BLOK 2: Mrežna latencija i točke loma upravljanja (T-13a – T-13e)
*(T-13a: 0 ms | T-13b: +50 ms | T-13c: +100 ms | T-13d: +200 ms | T-13e: +400 ms)*

### 👤 Odgovori Subjekta (Ivan Noršić):
- **Prag neprimjetnosti (+0 ms i +50 ms)**: Razlika nije neprimjetna; na +50 ms odmah se osjeti malo izraženije trzanje i blago kašnjenje robota. Ipak, to je i dalje potpuno upravljivo i očekivano ponašanje, s minimalnim efektivnim kašnjenjem.
- **Početak smetnje (+100 ms)**: Primjetno kašnjenje robota, posebno u točkama promjene smjera gibanja. Operater mora čekati robota da stigne u ekstremni položaj.
- **Točka loma i gubitak kontrole (+200 ms i +400 ms)**: Još veće kašnjenje, izrazito naglašeno u točkama promjene smjera. Javlja se nesigurnost pri izvođenju pokreta kroz točke zaustavljanja; operater mora čekati robota.
- **Strategija kompenzacije (*Move-and-Wait*)**: Da, točno se osjeti trenutak kada robot kasni i operater nesvjesno prelazi na strategiju "pomakni ruku $\rightarrow$ čekaj da robot dosegne poziciju".

### 👁️ Zapažanja Promatrača (Krešimir Hartl):
- **Sigurnost radnog prostora**: Do 100 ms sustav je siguran i predvidljiv bez potrebe za velikom kompenzacijom sa strane operatera.
- **Usklađenost čovjeka i stroja**: Na +200 ms i +400 ms operater je morao svjesno razmišljati i ulagati kognitivni napor da kompenzira nesavršenost sustava — pažljivo ciljati točke i čekati robota.

---

## BLOK 3: Kontrolirani gubitak paketa (T-14 – T-18)
*(T-14: 0% | T-15: 5% | T-16: 10% | T-17: 20% | T-18: 30%)*

### 👤 Subjekt (Ivan Noršić) & 👁️ Promatrač (Krešimir Hartl):
- **Otpornost na gubitak (5% – 20%)**: Već na 5% gubitka osjeti se blago smanjenje fluidnosti gibanja, ali minimalno te robot i dalje lijepo prati operatera. Na 10% gubitka trzanje postaje izraženije. Na 20% javljaju se još veća stajanja i diskontinuiteti.
- **Ponašanje na 30% gubitka (T-18)**: Jako primjetno trzanje i gubitak glatkoće; operater mora čekati robota, a tok gubi fluidnost teleoperacije.

---

## BLOK 4: Sigurnosni mehanizmi i incidentne situacije (T-08 – T-12b, T-20)

### 👤 Subjekt (Ivan Noršić) & 👁️ Promatrač (Krešimir Hartl):
- **Rate-limit / Ograničenje brzine (T-08)**: Robot glatko i polako odlazi u ekstrem pokreta, bez trzanja, unutar zadanog limita brzine (25 °/s). Primjetno je malo zaostajanje/kašnjenje kod nagle promjene smjera dok robot ne sustigne trajektoriju.
- **Range-limit / Ograničenje raspona (T-09)**: Robot se mirno zaustavlja na softverskim granicama radnog prostora ($\pm 25^\circ$) i čeka povratak ruke. Unutar dozvoljenog raspona gibanje se prati potpuno normalno.
- **Fail-safe na okluziju markera (T-10)**: 
  - Robot se trenutačno zaustavlja u trenutku okluzije.
  - *Ključno inženjersko zapažanje*: Zglobovi i relativni odnosi koji su se i dalje mogli izračunati nastavili su se pratiti (npr. pri zaklonjenoj nadlaktici, šaka se i dalje mogla kontrolirati).
  - Po uklanjanju okluzije, robot se glatko vraća u potpuno praćenje uz blagi početni prilagodni trzaj kako bi sustigao trenutni položaj ruke.
- **E-stop zaustavljanje (T-12a softverski / T-12b hardverski)**: Na pritisak fizičkog E-stopa robot se trenutačno zaustavlja i tok se prekida. Po deblokadi E-stop gljive komunikacija se normalno nastavlja.
- **Nagli pokreti / Step-odziv (T-20)**: Robot uspješno kompenzira nagle trzaje ruke, prati pokret, ali uz kontrolirano smanjenu akceleraciju radi zaštite mehaničke strukture i okoline.

---

## BLOK 5: Opći pHRI dojam, ergonomija i teleoperacija (T-02, T-03, Slobodna vožnja)

### 👤 Subjekt (Ivan Noršić):
- **Intuitivnost 6-DOF mimikrije**: Izrazito intuitivna kontrola robota preslikavanjem zglob-na-zglob. Navikavanje je iznimno brzo i prirodno, bez potrebe za dugotrajnim treningom.
- **Osjećaj "utjelovljenja" (*Embodiment*)**: U optimalnim uvjetima (niska latencija, One-Euro filtar) postojao je snažan osjećaj izravne kontrole, no ne kao doslovni tjelesni produžetak jer nema 1:1 povrata sile i napora. Doživljaj je bio poput izuzetno preciznog i prirodnog alata u ruci.
- **Fizički zamor**: Nakon ~5 minuta kontinuiranog rada držanje ispružene ruke u neutralnom/početnom položaju postaje zamorno za mišiće ramena i nadlaktice.
- **Kinematika zapešća vs lakat/rame**: Rotacija zapešća bila je vizualno pojačana na robotu jer je šaka na robotu dulja i rotacijski centri nisu u jednoj točki. Zbog toga su rotacije u ramenu i laktu bile znatno prirodnije od fleksije/aksijalne rotacije zapešća.

### 👁️ Promatrač (Krešimir Hartl):
- **Prednosti nad klasičnim sučeljima**: Sustav vjerno i intuitivno preslikava relativna gibanja ljudske ruke na robota. Uz nisku latenciju i robusno filtriranje postiže se siguran sustav s minimalnom krivuljom učenja u usporedbi s industrijskim teach pendantom ili joystickom.
- **Kolaborativni potencijal (pHRI)**: Izvrstan potencijal za demonstracijsko učenje i telemanipulaciju u opasnim/sterilnim okruženjima. Softverska ograničenja brzina, raspona i sila čine sustav sigurnim i predvidljivim. Zanimljiv smjer budućeg rada bio bi prijenos pokreta cijelog tijela na humanoidnog robota.
- **Anegdota s testiranja**: Ivan je tijekom slobodne demonstracije uspio s lakoćom dati "High five" ("dati pet") robotskoj šaci bez ikakvog napora ili nesigurnosti!
