Zadatak 2: Upravljanje zglobom Universal Robots robota pomoću OptiTrack sustava u
realnom vremenu
Kontekst i motivacija: U području fizičke interakcije čovjeka i robota (physical Human–
Robot Interaction, pHRI), jedan od temeljnih izazova je sigurno, stabilno i intuitivno
preslikavanje ljudskih pokreta na robotske kretnje. Za razliku od klasičnog programiranja
robota putem unaprijed definiranih putanja, pHRI sustavi omogućuju čovjeku da izravno
utječe na ponašanje robota kroz vlastite pokrete, čime se otvaraju mogućnosti prirodnije
suradnje, ali i značajni sigurnosni rizici.
Optički sustavi za praćenje pokreta, poput OptiTrack sustava, omogućuju precizno
mjerenje položaja i orijentacije dijelova ljudskog tijela u realnom vremenu. Međutim,
prijenos takvih mjerenja u robotski sustav nije trivijalan problem. Ljudski pokreti su
kontinuirani, često neglatki i podložni šumu, dok roboti zahtijevaju stabilne, ograničene i
sigurnosno provjerene naredbe. Uz to, mrežna komunikacija (npr. UDP streaming) uvodi
dodatne izazove u obliku kašnjenja, jittera i gubitka paketa.
Ova tema istražuje granice izravnog upravljanja robotom ljudskim pokretom, s posebnim
naglaskom na sigurnost, stabilnost i doživljaj kontrole u pHRI kontekstu.
Cilj seminara: dizajnirati i analizirati sustav koji omogućuje upravljanje jednim zglobom UR
robota na temelju pokreta ljudske ruke snimljene OptiTrack sustavom, te istražiti:
• koliko precizno i stabilno je moguće preslikati ljudski pokret na robota
• kako šum, kašnjenje i varijabilnost ljudskog pokreta utječu na sustav
• koje su tehničke i sigurnosne granice takvog upravljanja
• kako korisnik percipira razinu kontrole i sigurnosti u pHRI scenariju
Opis zadatka (zajednički okvir) - potrebno je razviti sustav koji u realnom vremenu:
• prima podatke o položaju markera ljudske ruke iz OptiTrack sustava
• iz tih podataka računa zakret određenog zgloba ruke
• mapira dobiveni zakret na odgovarajući zglob UR robota
• šalje izračunate vrijednosti robotu putem mrežne komunikacije
• Sustav mora raditi kontinuirano, uz jasno definirane granice sigurnog ponašanja.
Zadatak 2, Varijanta A – Srednje lakša razina – maksimalni broj bodova 40
Fokus ove varijante je na razvoju stabilnog i robusnog komunikacijsko-upravljačkog
sustava, bez izlaganja stvarnog robota potencijalno opasnim situacijama. Naglasak je na
obradi signala, mrežnoj komunikaciji i stabilnosti upravljanja u simulacijskom okruženju.
Faze rada:

1. Prikupljanje podataka iz OptiTrack sustava:
Potrebno je implementirati prijem podataka iz OptiTrack sustava koristeći UDP protokol.
Zahtjevi:
• prijem pozicija više markera u realnom vremenu
• identifikacija relevantnih markera za praćenje ljudske ruke
• obrada gubitka paketa i nepravilnog redoslijeda poruka
• analiza frekvencije uzorkovanja i njezina stabilnost
U izvješću je potrebno jasno opisati strukturu primljenih podataka i način njihove obrade.
2. Izračun zakreta zgloba:
Na temelju pozicija više markera potrebno je izračunati kut zakreta ljudskog zgloba (npr.
zapešće ili lakat). Zahtjevi:
• korištenje najmanje tri markera po segmentu
• matematički ispravan izračun kuta (vektorski pristup)
• analiza osjetljivosti izračuna na pogreške mjerenja
Potrebno je obrazložiti:
• koji se koordinatni sustav koristi
• kako se rješava problem singularnosti i nestabilnih konfiguracija
3. Filtriranje i obrada signala:
Budući da su OptiTrack podaci podložni šumu, potrebno je implementirati filtriranje
signala. Zahtjevi:
• implementacija barem jednog filtra (npr. pomični prosjek, low-pass filter)
• analiza utjecaja filtriranja na kašnjenje i stabilnost
• usporedba sirovih i filtriranih podataka
Cilj nije samo “ugladiti” signal, već razumjeti kompromis između odziva i stabilnosti.
4. Upravljanje URSim simulatorom:
Izračunati zakret mora se u realnom vremenu slati u URSim simulator. Zahtjevi:
• stabilno upravljanje bez oscilacija
• ograničavanje brzine promjene kuta
• sigurno ponašanje u slučaju gubitka podataka
Potrebno je demonstrirati da sustav može raditi kontinuirano bez destabilizacije simulacije.
5. Analiza i evaluacija:
U ovoj varijanti potrebno je analizirati:
• kašnjenje od ljudskog pokreta do reakcije robota
• stabilnost upravljanja kroz vrijeme
• osjetljivost sustava na nagle promjene pokreta
Zadatak 2, Varijanta B – Napredna razina – maksimalni broj bodova 60
Fokus rada: Napredna varijanta proširuje simulacijsko rješenje na stvarni UR robot, čime se
problem iz tehničkog izazova pretvara u pHRI sigurnosni problem. Ovdje fokus više nije
samo “radi li sustav”, već je li njegovo ponašanje sigurno, predvidivo i prihvatljivo za
čovjeka.
Faze rada:
6. Integracija sa stvarnim UR robotom:
Potrebno je implementirati upravljanje jednim zglobom stvarnog UR robota koristeći iste
podatke iz OptiTrack sustava. Zahtjevi:
• korištenje odgovarajućeg UR sučelja (URScript / RTDE / TCP)
• stabilno i glatko upravljanje bez trzaja
• sinkronizacija frekvencije OptiTracka i robota
7. Sigurnosni pipeline:
Obavezan dio ove varijante je implementacija višeslojnog sigurnosnog sustava. Sigurnosni
mehanizmi moraju uključivati:
• ograničenje maksimalne brzine zgloba
• ograničenje dopuštenog raspona gibanja (workspace limit)
• ponašanje u slučaju gubitka signala (fail-safe)
• emergency stop mehanizam
Potrebno je jasno obrazložiti zašto su odabrane granice sigurnosti i kako one utječu na
interakciju.
8. Analiza latencije i jittera:
U ovoj varijanti potrebno je provesti detaljnu analizu vremenskih karakteristika sustava.
Analiza uključuje:
• mjerenje ukupne latencije sustava
• varijacije kašnjenja (jitter)
• utjecaj mrežne komunikacije na stabilnost upravljanja
Rezultati se moraju prikazati grafički i interpretirati u kontekstu pHRI-a.
9. pHRI analiza i rasprava:
Ključni dio seminara je rasprava o sigurnosti i doživljaju interakcije. Potrebno je analizirati:
• kako kašnjenje utječe na osjećaj kontrole
• kada sustav postaje “neugodan” ili nesiguran za korisnika
• koje pogreške su prihvatljive, a koje nisu
• granicu između teleoperacije i autonomnog ponašanja robota
Analiza mora biti povezana s recentnom literaturom iz područja pHRI i sigurnosti
kolaborativnih robota.
