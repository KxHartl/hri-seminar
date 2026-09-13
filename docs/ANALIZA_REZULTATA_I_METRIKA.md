# DETALJNA TEHNIČKA ANALIZA REZULTATA I MJERENJA (Za autora)

Ovaj dokument daje preciznu, matematički i fizikalno utemeljenu raščlambu svih rezultata izmjerenih na robotu UR3e, kako bi autor imao 100% jasan uvid u svaku brojku koja se navodi u radu.

---

## 1. Razlika između latencije obrade (3--4 ms) i ukupnog kašnjenja (385 ms)

Jedan od najvažnijih koncepata u radu je razlikovanje **vremena izračuna (processing latency)** i **dinamičkog faznog kašnjenja (phase lag / end-to-end response)**:

### A. Latencija obrade jednog takta (3,0 -- 4,0 ms)
- **Što mjeri:** Vrijeme koje protekne od trenutka kada UDP paket s pozicijama markera stigne na mrežno sučelje računala, preko izračuna zglobnih kutova ($\operatorname{atan2}$ i kvaternioni), filtriranja, sigurnosne provjere (clamping/rate limit), do slanja RTDE paketa prema UR3e kontroleru.
- **Kako je izmjereno:** $t_\text{slanje\_robotu} - t_\text{primitak\_paketa}$ u svakom pojedinom taktu od 125 Hz.
- **Fizikalno značenje:** Upravljačka petlja troši samo 3 do 4 ms od raspoloživih 8,0 ms (za takt od 125 Hz). **Računalo nije usko grlo.**

### B. Ukupno dinamičko kašnjenje / fazni pomak ruka $\rightarrow$ robot (385 ms)
- **Što mjeri:** Vrijeme koje protekne od trenutka kada operater fizički pomakne ruku u prostoru do trenutka kada zglob robota dosegne odgovarajući kut.
- **Kako je izmjereno:** Vremenski pomak $\tau$ koji maksimizira međusobnu korelaciju (cross-correlation) između vremenskog niza kuta ruke i stvarnog kuta robota očitanog preko RTDE telemetrije.
- **Zašto je 385 ms, a ne 3 ms?** Zato što filtar i regulacijski krug robota unose **fazno kašnjenje** kako bi pokret bio gladak i siguran.

---

## 2. Točna aditivna dekompozicija kašnjenja na laktu (J3 = 385 ms)

Ukupno kašnjenje od 385 ms razlaže se na tri točno definirana fizikalna uzroka:

$$\tau_\text{ukupno} = \tau_\text{filtar} + \tau_\text{sigurnost} + \tau_\text{servo} = 200\text{ ms} + 73\text{ ms} + 112\text{ ms} = 385\text{ ms}$$

```
[Pokret ruke] 
     │
     ▼  (+200 ms)  -> One-Euro filtar uklanja šum i podrhtavanje (fc = 1.0 Hz)
[Filtrirani kut]
     │
     ▼  (+73 ms)   -> Sigurnosni sloj ograničava brzinu na naglim dijelovima pokreta
[Naredba robotu]
     │
     ▼  (+112 ms)  -> servoJ lookahead_time (100 ms) + elektromehanička dinamika motora
[Stvarni kut robota]
```

### Detalji pojedinih faza:
1. **Dinamika servoa robota ($\tau_\text{servo} = 112\text{ ms}$):**
   U pozivu funkcije `servoj(q, t=0.008, lookahead_time=0.100, gain=300)` zadan je `lookahead_time` od 100 ms. Robot namjerno interpolira putanju 100 ms unaprijed kako bi spriječio trzanje motora. Uz dinamiku pogona to daje točno 112,4 ms.
2. **Sigurnosni sloj ($\tau_\text{sigurnost} = 73\text{ ms}$):**
   Kada ruka ubrza brže od zadane maksimalne brzine zgloba ($150^\circ/\text{s}$ u normalnom radu ili $25^\circ/\text{s}$ u testu), sigurnosni algoritam zasićuje brzinu i pretvara skok u rampu, što unosi dodatnih 73 ms kašnjenja na vršnim dijelovima zamaha.
3. **Filtar signala ($\tau_\text{filtar} = 200\text{ ms}$):**
   One-Euro filtar s baznom frekvencijom $f_{c,\min} = 1{,}0\text{ Hz}$ pri mirnim i umjerenim pokretima jako zaglađuje signal. Fazni pomak niskopropusnog filtra prvog reda na 1 Hz iznosi oko 150--200 ms.

---

## 3. Zašto je efektivna frekvencija ulaza bila 31--73 Hz?

- Sustav OptiTrack Motive emitira poze na 120 Hz.
- Međutim, u upravljačkoj petlji na 125 Hz detektirano je da novi podaci ne stižu u svakom taktu (oko 40--60 % taktova imalo je zadržanu prethodnu vrijednost).
- **Uzrok u laboratoriju:** Mrežni promet laboratorija i konfiguracija UDP socket međuspremnika dovodili su do grupiranja paketa (bursting), pa je petlja trošila najnoviji paket, a na među-taktovima zadržavala zadnje stanje.
- **Posljedica:** One-Euro filtar je radio s efektivno duljim periodom uzorkovanja, što je pojačalo njegovo zaglađivanje i objasnilo zašto je fazni pomak filtra bio dominantan.

---

## 4. Analiza gubitka paketa (T5a do T5e)

- U laboratoriju je izvedeno 5 uzastopnih pokusa (T5a = 0%, T5b = 5%, T5c = 10%, T5d = 20%, T5e = 30%).
- Izmjerena starost signala (p95 signal age):
  - 0% gubitka $\rightarrow$ 7,5 ms
  - 5% gubitka $\rightarrow$ 8,9 ms
  - 10% gubitka $\rightarrow$ 12,0 ms
  - 20% gubitka $\rightarrow$ 15,6 ms
  - 30% gubitka $\rightarrow$ 20,1 ms
- Čak i pri 30% gubitka paketa, starost signala od 20,1 ms je daleko ispod sigurnosnog praga zaustavljanja od 150 ms, što dokazuje da protokol s punim stanjem u svakom paketu osigurava visoku robusnost.

---

## 5. Zbrajanje baznog i dodanog kašnjenja (Ukupno fizikalno kašnjenje do ~800 ms)

Pri ispitivanju utjecaja mrežnog kašnjenja (pokusi T4a do T4e), međuspremnik `DelayLine` zadržava okvire prije ulaska u kinematički izračun. Zato se umjetno dodano kašnjenje **direktno pribraja** postojećem dinamičkom odzivu sustava:

$$\tau_\text{ukupno} = \tau_\text{bazno} + \tau_\text{dodano} = 385\text{ ms} + \tau_\text{dodano}$$

| Pokus | Dodano kašnjenje | Bazno kašnjenje sustava | **Ukupno kašnjenje ($\tau_\text{ukupno}$)** | Ponašanje operatera |
| :--- | :---: | :---: | :---: | :--- |
| **T4a** | 0 ms | 385 ms | **385 ms** (~0,4 s) | Kontinuirano, prirodno vođenje |
| **T4b** | 50 ms | 385 ms | **435 ms** (~0,45 s) | Kontinuirano, uz blagu opreznost |
| **T4c** | 100 ms | 385 ms | **485 ms** (~0,5 s) | Usporavanje na točkama promjene smjera |
| **T4d** | 200 ms | 385 ms | **585 ms** (~0,6 s) | Prijelaz na *move-and-wait* |
| **T4e** | 400 ms | 385 ms | **785 ms** (~0,8 s) | **Gotovo 1 sekunda**; potpuno diskontinuiran rad |

### Zašto je ovo ključan uvid:
1. **Razrješenje prividnog neslaganja s literaturom:**
   - Radovi iz područja teleoperacije (npr. Louca i sur., 2024.) navode da operateri prelaze na strategiju *move-and-wait* tek iznad 500 ms do 1000 ms kašnjenja.
   - Kad bi se gledalo samo dodano kašnjenje (100–200 ms), činilo bi se da naš sustav degradira prerano.
   - No kad se uvaži da sustav već u bazi nosi 385 ms dinamičkog odziva, prijelaz se događa pri **500 do 600 ms ukupnog kašnjenja**, što se **savršeno podudara sa znanstvenom literaturom**!
2. **Zašto je robot na 400 ms djelovao "neupotrebljivo":**
   - Zato što je kašnjenje od pokreta ruke do stvarne reakcije robota iznosilo **785 ms (skoro 1 sekundu)**. Čovjek bi napravio pokret, robot bi tek nakon 0,8 s završio kretnju, što u potpunosti onemogućuje kontinuiranu vizualnu povratnu spregu.

---

## 6. Analiza okluzije markera (Pokus T-10 / T3c) — Egzaktni podaci

U teleometrijskoj datoteci `data/raw/lab_session_01092026_020000/telemetry/T-10.track.csv` zabilježeno je svih 3750 uzoraka (30 sekundi pokusa na 125 Hz).
Automatska analiza provedena skriptom `src/tools/analyze_occlusion.py` daje točne fizikalne trenutke:

- **Početak okluzije:** $t = 11{,}369\text{ s}$ (operater prekriva markere nadlaktice)
- **Kraj okluzije:** $t = 16{,}319\text{ s}$ (markeri ponovno postaju vidljivi kamerama)
- **Trajanje okluzije:** $\Delta t = 4{,}951\text{ s} \approx \mathbf{5{,}0\text{ sekundi}}$ (točno 617 uzastopnih taktova)
- **Zadržana vrijednost kuta J1:** $-3{,}86^\circ$

### Ponašanje pojedinih segmenata tijela:
- **Zglobovi J1, J2, J3 (rame i lakat):** **POTPUNO ZAMRZNUTI** (ravna linija). Budući da su markeri nadlaktice bili zaklonjeni, most drži zadnju valjanu pozu za to kruto tijelo.
- **Zglobovi J4, J5, J6 (zapešće i šaka):** **KONTINUIRANO AKTIVNI** (zglob J5 se kreće u rasponu od 2,41$^\circ$, J6 u rasponu od 2,93$^\circ$). Markeri šake nisu bili zaklonjeni pa sustav nesmetano prati njezino gibanje!

> **Napomena o ispravku grafa:** U ranijoj verziji skripte za crtanje žuti pojas okluzije bio je pogrešno postavljen na interval 9,0 s – 12,5 s umjesto na stvarni interval zamrzavanja. Ispravkom u `generate_report_figures.py` graf na slici 4.2c sada točno i precizno pokriva plato od $11{,}37\text{ s}$ do $16{,}32\text{ s}$.

---

## 7. Popis svih 21 izvedenih pokusa i videozapisa (Engleska nomenklatura)

U laboratoriju je izveden točno 21 pokus na robotu UR3e i snimljen u 21 videozapisu (od `test_02.mp4` do `test_22.mp4`):

| Br. | Oznaka | Interni CSV | Videozapis (`data/raw/lab_session_01092026_020000/camera/`) | Stvarni fizikalni sadržaj |
| :---: | :---: | :---: | :--- | :--- |
| 1 | **T1a** | `T-02` | `T1a_natural_tempo.mp4` | 6-DOF kinematičko oponašanje, prirodni tempo |
| 2 | **T1b** | `T-03` | `T1b_joint_walkthrough.mp4` | Izolirano gibanje zglob po zglob (pun raspon po kanalu) |
| 3 | **T2a** | `T-04` | `T2a_filter_one_euro.mp4` | Usporedba filtara: One-Euro (optimalan kompromis) |
| 4 | **T2b** | `T-05` | `T2b_filter_none.mp4` | Usporedba filtara: Bez filtra (nervozan, trzanje motora) |
| 5 | **T2c** | `T-06` | `T2c_filter_butterworth.mp4` | Usporedba filtara: Butterworth 2. reda (veliko kašnjenje) |
| 6 | **T2d** | `T-07` | `T2d_filter_ema.mp4` | Usporedba filtara: EMA ($\alpha=0{,}2$) |
| 7 | **T3a** | `T-08` | `T3a_rate_limit.mp4` | Sigurnost: ograničenje brzine na $25^\circ/\text{s}$ (745 zasićenih taktova) |
| 8 | **T3b** | `T-09` | `T3b_range_limit.mp4` | Sigurnost: ograničenje raspona na $\pm 25^\circ$ (406 zaustavljenih taktova) |
| 9 | **T3c** | `T-10` | `T3c_marker_occlusion.mp4` | Sigurnost: okluzija markera nadlaktice (5,0 s, 617 zadržanih taktova) |
| 10 | **T3d** | `T-12a` | `T3d_estop.mp4` | Sigurnost: E-stop (softverski stop na 10 s + teach pendant) |
| 11 | **T6** | `T-20` | `T6_step_response.mp4` | Dinamika: 5 naglih trzaja ruke (step response na robotu) |
| 12 | **T4a** | `T-13a` | `T4a_latency_0ms.mp4` | Latencijski sweep: dodano kašnjenje +0 ms |
| 13 | **T4b** | `T-13b` | `T4b_latency_50ms.mp4` | Latencijski sweep: dodano kašnjenje +50 ms |
| 14 | **T4c** | `T-13c` | `T4c_latency_100ms.mp4` | Latencijski sweep: dodano kašnjenje +100 ms |
| 15 | **T4d** | `T-13d` | `T4d_latency_200ms.mp4` | Latencijski sweep: dodano kašnjenje +200 ms |
| 16 | **T4e** | `T-13e` | `T4e_latency_400ms.mp4` | Latencijski sweep: dodano kašnjenje +400 ms |
| 17 | **T5a** | `T-14` | `T5a_packet_loss_0pct.mp4` | Otpornost na gubitak: 0 % |
| 18 | **T5b** | `T-15` | `T5b_packet_loss_5pct.mp4` | Otpornost na gubitak: 5 % |
| 19 | **T5c** | `T-16` | `T5c_packet_loss_10pct.mp4` | Otpornost na gubitak: 10 % |
| 20 | **T5d** | `T-17` | `T5d_packet_loss_20pct.mp4` | Otpornost na gubitak: 20 % |
| 21 | **T5e** | `T-18` | `T5e_packet_loss_30pct.mp4` | Otpornost na gubitak: 30 % |

---

## 8. Znanstvena metodologija: Eksperiment kao temelj + analitička simulacija za izolaciju

U radu se dosljedno primjenjuje rigorozan inženjerski pristup:
1. **Fizikalni pokus na robotu je neprikosnoveni temelj:** Svaki redak tablica i tvrdnji u radu potječe iz stvarnih mjerenja na kolaborativnom robotu UR3e uz prisustvo operatera u laboratoriju.
2. **Komplementarna analitička simulacija služi za izolaciju utjecaja:**
   - **Kod gubitka paketa:** Pokusi T5a--T5e izvedeni su fizički na robotu, a komplementarna evaluacija nad identičnom baznom putanjom T5a omogućila je determinističko uklanjanje varijance ljudskog pokreta kako bi se dokazao čist mrežni utjecaj.
   - **Kod dinamičkog odziva:** Pokus T6 na robotu dao je stvarni odziv na 5 naglih pokreta čovjeka, dok analitički odziv na idealni skok i impuls (slika 4.3b) matematički dokazuje granične prijenosne karakteristike kaskade filtra i limitera.


