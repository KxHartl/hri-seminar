"""Quick connectivity check to Motive using the OFFICIAL NatNet SDK client.

Reports whether the command channel connects (ServerInfo) and whether data frames
arrive. Decisive cross-check: if even this official client fails, the problem is
Motive config/network, not our code.

Setup:  set NATNET_SDK=...\\NatNetSDK\\Samples\\PythonClient  (if not default)
Usage:  python testing/lab/diag/sdk_probe.py <server_ip> <client_ip> <multicast 1|0>
        # lab: works with multicast=0 (unicast). Multicast gave 0 frames (switch/IGMP).
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
    sys.exit(f"NatNetClient nije nađen u '{SDK}'. Postavi env NATNET_SDK.")

server = sys.argv[1] if len(sys.argv) > 1 else "192.168.40.31"
client = sys.argv[2] if len(sys.argv) > 2 else "192.168.40.30"
mcast = (sys.argv[3] if len(sys.argv) > 3 else "0") == "1"

frames = [0]
nc = NatNetClient()
nc.set_client_address(client)
nc.set_server_address(server)
nc.set_use_multicast(mcast)
nc.new_frame_listener = lambda d: frames.__setitem__(0, frames[0] + 1)

print(f"SDK PROBE server={server} client={client} multicast={mcast}")
print("run() ->", nc.run())
time.sleep(3.0)
print("connected() ->", nc.connected())
print("application ->", nc.get_application_name())
print("MotiveVer   ->", nc.get_server_version())
print("NatNetVer   ->", nc.get_nat_net_version_server())
print("frames/3s   ->", frames[0])
try:
    nc.shutdown()
except Exception:  # noqa: BLE001
    pass
