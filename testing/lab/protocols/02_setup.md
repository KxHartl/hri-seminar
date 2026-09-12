# 01 — SETUP u labosu (korak po korak)

Popuni prvo ovu tablicu (sazna na licu mjesta):

| Parametar | Vrijednost (upiši) |
|---|---|
| UR3e IP | `__________________` |
| Motive (NatNet server) IP | `__________________` |
| Lokalni NIC IP (laptop) | `__________________` |
| NatNet verzija | `__________________` |
| Unicast / Multicast | `__________________` |
| Imena markera u Motive | `zapesce? srednji? mali? palac?` |
| Robot+Motive na istom PC kao pipeline? | `DA / NE` |

## A. Robot (UR3e)
1. Uključi robota, **Power on** → **Brake release** (PolyScope).
2. Postavi **payload** i **TCP** (Installation → General). Za J4 fleksiju nije kritično, ali postavi točno.
3. **Remote Control ON**: hamburger (≡) → Settings → System → Remote Control → Enable; pa
   gornji desni prekidač → **Remote Control**.
4. Provjeri da je radni prostor **prazan**.

## B. Mreža
1. Spoji laptop na istu mrežu kao robot i Motive.
2. Provjeri dohvatljivost robota:
   ```
   ping <UR3e IP>
   ```
3. (Faza 2) Provjeri dohvatljivost Motivea i da NatNet stream radi (u Motive: Streaming pane ON,
   zabilježi multicast/unicast + verziju).

## C. Provjera RTDE veze + mali sweep (OBVEZNO prije ičega)
> Prazan prostor! Ovo pomakne J4 ±5°.
```
.venv/Scripts/python -m src.tools.check_ursim --ip <UR3e IP>
```
- Očekivano: `RTDE povezan ... robot mode=7 ... Sweep završen, servoStop OK`.
- Ako javi *"enable remote control"* → vrati se na A.3.
- Zapiši pročitani `home_q` (i J4 home kut) u `run_log`.

## D. Postavi sigurnost (konzervativno za prvi dan)
U `src/config/default.yaml` (ili lab config):
```yaml
safety:
  max_joint_speed_dps: 20      # kreni nisko
  joint_range_dps: 30          # ±30° oko home
  signal_timeout_s: 0.15
```
- Provjeri smjer/razmjer na malim pokretima prije punog testa (`mapping.gain`, `mapping.invert`).

## E. (Faza 2) Motive marker set
- Marker set mora dati markere čija imena sadrže `zapesce`, `srednji`, `mali` (+`palac`).
- Ako se imena razlikuju, uredi `src/config/default.yaml` → `source.live.marker_name_map`
  (naše ime → substring stvarnog imena), npr. `zapesce: wrist`.

Kad je sve gore ✅ → idi na `02_TEST_PROTOCOL.md`.
