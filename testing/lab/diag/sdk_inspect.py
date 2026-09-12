"""Inspect Motive's live stream via the OFFICIAL NatNet SDK client.

Prints marker-set names, per-marker names (ORDER matters for index mapping) and
one frame's positions. Use this once the hand/arm marker set exists in Motive to
read the exact names/order and build the name->index mapping for the live source.

The hand-rolled client in ``src/optitrack/natnet`` cannot parse NatNet 4.0
model-definitions (no per-dataset size field, arbitrary dataset order), so we use
OptiTrack's SDK for the description/handshake. Frame transport itself is
confirmed working with our own parsers (see ``natnet_unicast_probe.py``).

Setup:
    set NATNET_SDK=C:\\path\\to\\NatNetSDK\\Samples\\PythonClient   (if not default)
Usage:
    python testing/lab/diag/sdk_inspect.py <server_ip> <client_ip>
    # lab default: server=192.168.40.31 (Motive)  client=192.168.40.30 (this PC)
"""
import os
import sys
import time

DEFAULT_SDK = r"C:\Users\KHartl\Downloads\NatNet_SDK_4.5_windows\NatNetSDK\Samples\PythonClient"
SDK = os.environ.get("NATNET_SDK", DEFAULT_SDK)
sys.path.insert(0, SDK)
try:
    from NatNetClient import NatNetClient  # noqa: E402
except ImportError:
    sys.exit(f"NatNetClient nije nađen u '{SDK}'. Postavi env NATNET_SDK na "
             f"...\\NatNetSDK\\Samples\\PythonClient")


def _s(b):
    return b.decode("utf-8", "replace") if isinstance(b, (bytes, bytearray)) else str(b)


server = sys.argv[1] if len(sys.argv) > 1 else "192.168.40.31"
client = sys.argv[2] if len(sys.argv) > 2 else "192.168.40.30"

desc_holder, frame_holder = {}, {}


def on_desc(desc):
    desc_holder["d"] = desc


def on_frame(data_dict):
    if "mocap_data" in data_dict and "f" not in frame_holder:
        frame_holder["f"] = data_dict["mocap_data"]


nc = NatNetClient()
nc.set_client_address(client)
nc.set_server_address(server)
nc.set_use_multicast(False)            # unicast (confirmed working in lab)
nc.data_descriptions_listener = on_desc
nc.new_frame_with_data_listener = on_frame

print(f"INSPECT server={server} client={client} unicast")
nc.run()
time.sleep(1.0)
nc.send_request(nc.command_socket, nc.NAT_REQUEST_MODELDEF, "",
                (server, nc.command_port))
time.sleep(2.0)

print("\n=== DATA DESCRIPTIONS (marker sets) ===")
d = desc_holder.get("d")
if d is None:
    print("  (nema descriptiona — je li streaming/marker-set uključen?)")
else:
    for ms in getattr(d, "marker_set_list", []):
        names = [_s(n) for n in ms.marker_names_list]
        print(f"  set '{_s(ms.name)}' ({len(names)} markera): {names}")

print("\n=== JEDAN FRAME (marker setovi + pozicije, metri) ===")
f = frame_holder.get("f")
if f is None or f.marker_set_data is None:
    print("  (nema frame podataka)")
else:
    for md in f.marker_set_data.marker_data_list:
        pts = md.marker_pos_list
        print(f"  '{_s(md.model_name)}' ({len(pts)} mk):")
        for i, p in enumerate(pts):
            print(f"      [{i}] {tuple(round(c, 4) for c in p)}")
try:
    nc.shutdown()
except Exception:  # noqa: BLE001
    pass
