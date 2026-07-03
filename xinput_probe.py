"""
xinput_probe.py — poll XInput slots 0-3 directly via XInputGetState,
the same API games use. Shows which slots are connected and live state.
Run alongside wuwa_kb_pad.py, hold keys, watch the values.
"""

import ctypes
import time

xinput = None
for dll in ("XInput1_4.dll", "xinput1_3.dll", "XInput9_1_0.dll"):
    try:
        xinput = ctypes.windll.LoadLibrary(dll)
        print(f"using {dll}")
        break
    except OSError:
        continue
if xinput is None:
    raise SystemExit("no XInput DLL found")


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [("dwPacketNumber", ctypes.c_uint), ("Gamepad", XINPUT_GAMEPAD)]


print("polling slots 0-3 — Ctrl+C to quit")
while True:
    line = []
    for slot in range(4):
        state = XINPUT_STATE()
        res = xinput.XInputGetState(slot, ctypes.byref(state))
        if res == 0:  # ERROR_SUCCESS = connected
            g = state.Gamepad
            line.append(
                f"slot{slot}: pkt={state.dwPacketNumber:8d} btn={g.wButtons:04x} LT={g.bLeftTrigger:3d} RT={g.bRightTrigger:3d} "
                f"LX={g.sThumbLX:6d} LY={g.sThumbLY:6d} RX={g.sThumbRX:6d} RY={g.sThumbRY:6d}"
            )
        else:
            line.append(f"slot{slot}: ---")
    print(" | ".join(line), end="\r", flush=True)
    time.sleep(0.05)