# NatNet / Motive live diagnostics

Diagnostički alati za živi OptiTrack put (Motive → naš kod), validirani u labosu
2026-06-26. Pokreni iz korijena repozitorija s `.venv` Pythonom.

## Lab mreža (potvrđeno)
| Uloga | IP |
|---|---|
| Ovaj PC (klijent) | `192.168.40.30` |
| Motive PC | `192.168.40.31` (+ ima i `192.168.0.100`) |
| Robot UR3e (od 2026-08-31; ranije CB3 na `.27`) | `192.168.40.50` |

Svi na **istom switchu**. ⚠️ PC ima i drugu karticu `Ethernet 4` (`192.168.40.22`)
na istoj podmreži — povremeno muti rutiranje/multicast; idealno ugasiti.

## Motive postavke (potvrđeno da rade)
- **Data Streaming = ON**, Local Interface = **192.168.40.31**
- **Transmission = Unicast** (multicast je dao 0 okvira — switch/IGMP); unicast = 120 Hz
- Stream Markers + Marker Sets = ON
- Motive **3.0.1**, NatNet **4.0**

## Alati
| Skripta | Što radi |
|---|---|
| `sdk_probe.py` | Brza provjera veze preko **službenog** SDK klijenta (ground-truth). |
| `natnet_unicast_probe.py` | Transport preko **naših** parsera (NAT_CONNECT+keepalive). ~480 okvira/4s. |
| `sdk_inspect.py` | **Najvažnije sutra**: ispiše imena marker-setova, imena markera (redoslijed) i pozicije. |

```bash
# SDK ground-truth (unicast):
.venv/Scripts/python testing/lab/diag/sdk_probe.py 192.168.40.31 192.168.40.30 0
# naš transport:
.venv/Scripts/python testing/lab/diag/natnet_unicast_probe.py 192.168.40.31 192.168.40.30
# inspekcija marker-setova (kad je ruka/segmenti u sceni):
.venv/Scripts/python testing/lab/diag/sdk_inspect.py 192.168.40.31 192.168.40.30
```

SDK putanja preko env varijable (ako nije default):
`set NATNET_SDK=C:\path\to\NatNetSDK\Samples\PythonClient`

## Ključni nalaz (zašto SDK za model-def)
Naš `src/optitrack/natnet` parser **ne čita NatNet 4.0 model-definicije**
(nema per-dataset size polja prije 4.1, dataseti u proizvoljnom redoslijedu).
Transport (frameovi) radi s našim parserima; imena markera vadimo preko SDK-a.
Odluka: živi izvor graditi na SDK klijentu. Detalji: `testing/lab/protocols/06_live_optitrack.md`.
