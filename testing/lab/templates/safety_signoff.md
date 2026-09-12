# Sigurnosni checklist po sesiji (potpiši prije gibanja robota)

Datum: __________  Sudionici: ______________________  Robot: UR3e  IP: __________

## Prije prvog pokreta
- [ ] Radni prostor robota **prazan** (nema ljudi/predmeta u dosegu).
- [ ] **Hardverski e-stop** lociran, dostupan i **testiran** (pritisni → robot ne reagira na naredbe).
- [ ] Konzervativne granice u configu: `max_joint_speed_dps ≤ 20`, `joint_range_dps ≤ 30`.
- [ ] `signal_timeout_s` postavljen (fail-safe), npr. 0.15.
- [ ] Payload/TCP postavljeni u PolyScope.
- [ ] `check_ursim` sweep prošao bez incidenta.
- [ ] Provjeren smjer gibanja na malom pokretu (nije obrnut/nekontroliran).

## Tijekom rada
- [ ] Jedna osoba na e-stopu kad robot radi.
- [ ] Granice se otpuštaju **postupno**, uz provjeru nakon svake promjene.
- [ ] Čovjek ulazi u prostor (pHRI) **tek** nakon potvrde stabilnosti i s e-stopom.

## Eskalacija granica (zabilježi)
| Korak | max_speed [°/s] | range [°] | OK? | napomena |
|-------|-----------------|-----------|-----|----------|
| 1 | 20 | 30 |  |  |
| 2 | 30 | 45 |  |  |
| 3 | ... | ... |  |  |

Potpis odgovorne osobe: ______________________
